#!/usr/bin/env python3
import argparse
import csv
import functools
import http.server
import ipaddress
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import threading
import time

SERVER='192.168.9.20'
ALLOWED='192.168.9.10'
DENIED='192.168.9.11'
GROUP='SiMZIIS-Lab6-V9'

def psquote(value):
    return "'"+str(value).replace("'","''")+"'"

def model(policy,direction,remote,port=None,program='python',protocol='TCP',icmp_type=None):
    if policy=='F' and direction=='Inbound' and protocol=='ICMPv4' and icmp_type==8:
        return False
    if direction=='Outbound':
        if policy=='D': return program=='python'
        if policy=='E': return program=='python' and remote==ALLOWED and protocol=='TCP' and port==80
        return True
    if policy=='A': return protocol=='TCP' and port==445 and remote==ALLOWED
    if policy=='B': return protocol=='TCP' and port==80
    if policy=='C': return protocol=='TCP' and port==80 and remote==ALLOWED
    if policy=='F': return protocol=='TCP' and port==80
    return False

def model_cases():
    return [
        ('A','Inbound',ALLOWED,445,'python','TCP',None,True),
        ('A','Inbound',DENIED,445,'python','TCP',None,False),
        ('A','Inbound',ALLOWED,80,'python','TCP',None,False),
        ('B','Inbound',ALLOWED,80,'python','TCP',None,True),
        ('B','Inbound',DENIED,80,'python','TCP',None,True),
        ('B','Inbound',ALLOWED,8080,'python','TCP',None,False),
        ('C','Inbound',ALLOWED,80,'python','TCP',None,True),
        ('C','Inbound',DENIED,80,'python','TCP',None,False),
        ('C','Inbound',ALLOWED,8080,'python','TCP',None,False),
        ('D','Outbound',ALLOWED,80,'python','TCP',None,True),
        ('D','Outbound',ALLOWED,8080,'python','TCP',None,True),
        ('D','Outbound',ALLOWED,80,'powershell','TCP',None,False),
        ('E','Outbound',ALLOWED,80,'python','TCP',None,True),
        ('E','Outbound',ALLOWED,8080,'python','TCP',None,False),
        ('E','Outbound',DENIED,80,'python','TCP',None,False),
        ('E','Outbound',ALLOWED,80,'powershell','TCP',None,False),
        ('E','Outbound',ALLOWED,80,'python','UDP',None,False),
        ('F','Inbound',ALLOWED,None,'python','ICMPv4',8,False),
        ('F','Inbound',DENIED,None,'python','ICMPv4',8,False),
        ('F','Inbound',ALLOWED,80,'python','TCP',None,True),
    ]

def simulate(out):
    rows=[]
    for i,case in enumerate(model_cases(),1):
        policy,direction,remote,port,program,protocol,itype,expected=case
        actual=model(*case[:-1])
        if actual != expected: raise AssertionError(case)
        rows.append(dict(case=i,policy=policy,direction=direction,remote=remote,port=port,
                         program=program,protocol=protocol,icmp_type=itype,
                         expected=expected,actual=actual,status='MODEL_PASS'))
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    with Path(out).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    print(f'{len(rows)} MODEL_PASS. Проверена модель, Windows-стенд не запускался.')

SETUP = r'''#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'
Import-Module SmbShare
$share = 'Lab6Share'
$user = 'lab6_reader'
$folder = 'C:\Lab6Share'
if ((Get-SmbShare -Name $share -ErrorAction SilentlyContinue) -or
    (Get-LocalUser -Name $user -ErrorAction SilentlyContinue) -or (Test-Path $folder)) {
    throw 'Lab resources already exist. Inspect them before repeating setup.'
}
$password = Read-Host 'Password for the temporary lab6_reader account' -AsSecureString
New-LocalUser -Name $user -Password $password -Description 'Temporary Lab6 account'
New-Item -ItemType Directory -Path $folder | Out-Null
Set-Content -Path "$folder\readme.txt" -Value 'Lab6 variant 9 shared resource' -Encoding UTF8
$account = "$env:COMPUTERNAME\$user"
& icacls.exe $folder /grant "${account}:(OI)(CI)RX"
if ($LASTEXITCODE -ne 0) { throw 'NTFS permission setup failed' }
New-SmbShare -Name $share -Path $folder -ReadAccess $account | Out-Null
Get-SmbShare -Name $share | Format-List
Get-SmbShareAccess -Name $share | Format-Table
Write-Host 'Share is ready; apply policy A separately. SMB1 is not required.'
'''

APPLY = r'''#Requires -RunAsAdministrator
param(
    [Parameter(Mandatory=$true)][ValidateSet('A','B','C','D','E','F')][string]$Policy,
    [Parameter(Mandatory=$true)][string]$PythonExe,
    [switch]$IsolatedLabVM
)
$ErrorActionPreference = 'Stop'
if (-not $IsolatedLabVM) { throw 'Run only from console of an isolated lab VM with -IsolatedLabVM.' }
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw 'Python executable not found' }
Import-Module NetSecurity
$group = 'SiMZIIS-Lab6-V9'
$backup = Join-Path $PSScriptRoot 'baseline.wfw'
$evidence = Join-Path $PSScriptRoot ('evidence\' + $Policy + '_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Force -Path $evidence | Out-Null
$gpo = @(Get-NetFirewallRule -PolicyStore ActiveStore | Where-Object {
    $_.Enabled -eq 'True' -and $_.PolicyStoreSourceType -eq 'GroupPolicy'
})
if ($gpo.Count -gt 0) { throw 'Active GPO rules found; use an unmanaged standalone lab VM.' }
if (-not (Test-Path $backup)) {
    & netsh.exe advfirewall export $backup | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Backup failed; no changes applied.' }
}
Start-Transcript -Path (Join-Path $evidence 'apply.txt') | Out-Null
try {
    Get-NetFirewallRule -PolicyStore PersistentStore | Where-Object { $_.Enabled -eq 'True' } |
        Disable-NetFirewallRule
    Get-NetFirewallRule -PolicyStore PersistentStore -Group $group -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule
    $outbound = if ($Policy -in @('D','E')) { 'Block' } else { 'Allow' }
    Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled True `
        -DefaultInboundAction Block -DefaultOutboundAction $outbound `
        -LogAllowed True -LogBlocked True -LogMaxSizeKilobytes 16384
    $common = @{Group=$group;Profile='Any';Enabled='True';PolicyStore='PersistentStore'}
    switch ($Policy) {
        'A' { New-NetFirewallRule @common -DisplayName 'Lab6 A SMB from allowed peer' `
              -Direction Inbound -Action Allow -Protocol TCP -LocalPort 445 -RemoteAddress '192.168.9.10' }
        'B' { New-NetFirewallRule @common -DisplayName 'Lab6 B HTTP any peer' `
              -Direction Inbound -Action Allow -Protocol TCP -LocalPort 80 }
        'C' { New-NetFirewallRule @common -DisplayName 'Lab6 C HTTP allowed peer' `
              -Direction Inbound -Action Allow -Protocol TCP -LocalPort 80 -RemoteAddress '192.168.9.10' }
        'D' { New-NetFirewallRule @common -DisplayName 'Lab6 D Python outbound' `
              -Direction Outbound -Action Allow -Program $PythonExe }
        'E' { New-NetFirewallRule @common -DisplayName 'Lab6 E Python peer port' `
              -Direction Outbound -Action Allow -Program $PythonExe -Protocol TCP `
              -RemoteAddress '192.168.9.10' -RemotePort 80 }
        'F' {
              New-NetFirewallRule @common -DisplayName 'Lab6 F HTTP control' `
                -Direction Inbound -Action Allow -Protocol TCP -LocalPort 80
              New-NetFirewallRule @common -DisplayName 'Lab6 F deny echo IPv4' `
                -Direction Inbound -Action Block -Protocol ICMPv4 -IcmpType 8
              New-NetFirewallRule @common -DisplayName 'Lab6 F deny echo IPv6' `
                -Direction Inbound -Action Block -Protocol ICMPv6 -IcmpType 128
        }
    }
    & (Join-Path $PSScriptRoot 'export_evidence.ps1') -OutDir $evidence
    Write-Host "Policy $Policy applied. Save client probes to $evidence. Restore with restore.ps1."
} catch {
    Write-Warning 'Apply failed. Restoring baseline firewall policy.'
    & netsh.exe advfirewall import $backup | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Warning 'Automatic restore failed; restore from VM snapshot.' }
    throw
} finally { Stop-Transcript | Out-Null }
'''

EXPORT = r'''param([Parameter(Mandatory=$true)][string]$OutDir)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
Get-NetFirewallProfile -PolicyStore ActiveStore | Select-Object Name,Enabled,DefaultInboundAction,DefaultOutboundAction,LogFileName |
    Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $OutDir 'profiles.csv')
Get-NetIPAddress | Select-Object InterfaceAlias,IPAddress,PrefixLength,AddressFamily |
    Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $OutDir 'addresses.csv')
$rows = foreach ($r in (Get-NetFirewallRule -PolicyStore ActiveStore | Where-Object { $_.Enabled -eq 'True' })) {
    $port = $r | Get-NetFirewallPortFilter
    $address = $r | Get-NetFirewallAddressFilter
    $app = $r | Get-NetFirewallApplicationFilter
    [pscustomobject]@{Name=$r.DisplayName;Group=$r.Group;Direction=$r.Direction;Action=$r.Action;
        Source=$r.PolicyStoreSourceType;Protocol=$port.Protocol;LocalPort=($port.LocalPort -join ',');
        RemotePort=($port.RemotePort -join ',');RemoteAddress=($address.RemoteAddress -join ',');
        Program=$app.Program;IcmpType=($port.IcmpType -join ',')}
}
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $OutDir 'active_rules.csv')
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress,LocalPort,OwningProcess |
    Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $OutDir 'listeners.csv')
& netsh.exe advfirewall export (Join-Path $OutDir 'effective_local_policy.wfw') | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Policy export failed' }
'''

RESTORE = r'''#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'
$backup = Join-Path $PSScriptRoot 'baseline.wfw'
if (-not (Test-Path $backup)) { throw 'No baseline.wfw found' }
& netsh.exe advfirewall import $backup
if ($LASTEXITCODE -ne 0) { throw 'Restore failed' }
Write-Host 'Original firewall policy restored. baseline.wfw retained.'
'''

PROBE_PS = r'''param([string]$HostAddress='192.168.9.10',[int]$Port=80,[string]$SourceAddress='',
    [string]$Expected='ALLOW',[string]$OutputCsv='.\powershell_probe.csv')
$client = New-Object System.Net.Sockets.TcpClient
$watch = [System.Diagnostics.Stopwatch]::StartNew()
$connected = $false
$errorText = ''
try {
    if ($SourceAddress) {
        $endpoint = New-Object System.Net.IPEndPoint ([System.Net.IPAddress]::Parse($SourceAddress)),0
        $client.Client.Bind($endpoint)
    }
    $task = $client.ConnectAsync($HostAddress,$Port)
    if (-not $task.Wait(3000)) { throw 'Timeout' }
    $connected = $client.Connected
} catch { $errorText = $_.Exception.Message }
finally { $client.Dispose(); $watch.Stop() }
[pscustomobject]@{Time=(Get-Date -Format o);Program=(Get-Process -Id $PID).Path;Remote=$HostAddress;
    Port=$Port;Source=$SourceAddress;Connected=$connected;Expected=$Expected;Seconds=$watch.Elapsed.TotalSeconds;
    Error=$errorText} | Export-Csv -Append -NoTypeInformation -Encoding UTF8 $OutputCsv
Write-Host "Connected=$connected Expected=$Expected Error=$errorText"
'''

def generate(out):
    root=Path(out);root.mkdir(parents=True,exist_ok=True)
    scripts={'setup_share.ps1':SETUP,'apply_policy.ps1':APPLY,'export_evidence.ps1':EXPORT,
             'restore.ps1':RESTORE,'probe_powershell.ps1':PROBE_PS}
    for name,content in scripts.items():
        (root/name).write_text(content,encoding='utf-8-sig')
    print(f'Созданы {len(scripts)} сценариев в {root.resolve()}')

def probe(args):
    started=time.perf_counter();connected=False;error=''
    try:
        ipaddress.ip_address(args.host)
        if args.source:ipaddress.ip_address(args.source)
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
            s.settimeout(args.timeout)
            if args.source:s.bind((args.source,0))
            s.connect((args.host,args.port));connected=True
    except (OSError,ValueError) as exc:error=str(exc)
    row=dict(time=time.strftime('%Y-%m-%dT%H:%M:%S'),program=sys.executable,remote=args.host,
             port=args.port,source=args.source,connected=connected,expected=args.expect,
             seconds=time.perf_counter()-started,error=error,
             matches_expectation=connected==(args.expect=='ALLOW'))
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True);exists=path.exists()
    with path.open('a',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=row)
        if not exists:w.writeheader()
        w.writerow(row)
    print(json.dumps(row,ensure_ascii=False,indent=2))
    return 0 if row['matches_expectation'] else 1

def serve(args):
    root=Path(args.directory);root.mkdir(parents=True,exist_ok=True)
    (root/'lab6.txt').write_text('Lab6 variant 9 test endpoint',encoding='utf-8')
    handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
    servers=[]
    try:
        for port in args.ports:
            server=http.server.ThreadingHTTPServer((args.bind,port),handler);servers.append(server)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            print(f'HTTP listening {args.bind}:{port}',flush=True)
        threading.Event().wait()
    except KeyboardInterrupt:pass
    finally:
        for server in servers:server.shutdown();server.server_close()

def main():
    parser=argparse.ArgumentParser(description='ЛР6, вариант 9. Генератор PowerShell-сценариев Windows Firewall и TCP-пробы.\nБез подкоманды apply настройки ОС не меняются. simulate проверяет только\nлогическую модель правил; это НЕ доказательство работы Windows Firewall.\nPython 3.10+, стандартная библиотека. PowerShell 5.1, права администратора.\n')
    sub=parser.add_subparsers(dest='command',required=True)
    g=sub.add_parser('generate');g.add_argument('--out',default='results/lab6/windows')
    s=sub.add_parser('simulate');s.add_argument('--out',default='results/lab6/model_checks.csv')
    a=sub.add_parser('apply');a.add_argument('--policy',choices=list('ABCDEF'),required=True)
    a.add_argument('--scripts',default='results/lab6/windows');a.add_argument('--isolated-lab-vm',action='store_true')
    p=sub.add_parser('probe');p.add_argument('--host',required=True);p.add_argument('--port',type=int,required=True)
    p.add_argument('--source',default='');p.add_argument('--expect',choices=['ALLOW','BLOCK'],required=True)
    p.add_argument('--timeout',type=float,default=3);p.add_argument('--out',default='results/lab6/probes.csv')
    s=sub.add_parser('serve');s.add_argument('--bind',default='0.0.0.0');s.add_argument('--ports',type=int,nargs='+',default=[80,8080])
    s.add_argument('--directory',default='results/lab6/www')
    args=parser.parse_args()
    if args.command=='generate':generate(args.out)
    elif args.command=='simulate':simulate(args.out)
    elif args.command=='probe':return probe(args)
    elif args.command=='serve':serve(args)
    else:
        if platform.system()!='Windows':parser.error('Настройка брандмауэра доступна только на Windows')
        if not args.isolated_lab_vm:parser.error('Требуется --isolated-lab-vm и запуск из консоли тестовой VM')
        path=Path(args.scripts)/'apply_policy.ps1'
        if not path.exists():parser.error('Сначала выполните generate')
        return subprocess.call(['powershell.exe','-NoProfile','-File',str(path.resolve()),
                                '-Policy',args.policy,'-PythonExe',sys.executable,'-IsolatedLabVM'])
    return 0

if __name__=='__main__':raise SystemExit(main())
