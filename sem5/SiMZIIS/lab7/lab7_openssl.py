import tempfile
import subprocess as s, os, time, statistics as st, pathlib as p
results_dir = tempfile.mkdtemp(prefix='lab7_openssl_', dir=os.getcwd())
print('Файлы эксперимента:', results_dir, flush=True)
os.chdir(results_dir)

def o(*a):
 return s.check_output(['openssl',*a],text=True)
print(o('version').strip(),flush=True)
print(o('list','-providers').strip(),flush=True)
print('CLI help:',s.run(['openssl','help'],capture_output=True).returncode,flush=True)
p.Path('note.txt').write_bytes(b'OpenSSL lab 7; variant 9.\n')
p.Path('sample.bin').write_bytes(bytes(range(128)))
p.Path('block.bin').write_bytes(bytes(range(256))*4096)
o('genpkey','-algorithm','RSA','-pkeyopt','rsa_keygen_bits:2048','-out','rsa.pem')
o('genpkey','-algorithm','EC','-pkeyopt','ec_paramgen_curve:P-256','-out','ec.pem')
for k in ('rsa','ec'):o('pkey','-in',k+'.pem','-pubout','-out',k+'-pub.pem')
o('req','-new','-x509','-key','rsa.pem','-sha256','-days','30','-subj','/CN=lab7.local','-addext','subjectAltName=DNS:lab7.local','-addext','basicConstraints=critical,CA:FALSE','-out','cert.pem')
print(o('x509','-in','cert.pem','-noout','-subject','-issuer','-serial','-dates','-fingerprint','-sha256'))
print(o('verify','-check_ss_sig','-trusted','cert.pem','cert.pem'))
for a,n in [('aes-256-cbc',32),('des-cbc',8),('chacha20',32)]:
 key=o('rand','-hex',str(n)).strip()
 for f in ('note.txt','sample.bin','block.bin'):
  iv=o('rand','-hex',str(8 if a=='des-cbc' else 16)).strip()
  args=['enc','-'+a,'-provider','default','-provider','legacy','-K',key,'-iv',iv]
  def m(decrypt):
   times=[]
   for _ in range(15 if f=='block.bin' else 1):
    t=time.perf_counter(); o(*args,*(['-d','-in','cipher','-out','restored'] if decrypt else ['-in',f,'-out','cipher'])); times.append((time.perf_counter()-t)*1000)
   return round(st.median(times),3)
  e,d=m(False),m(True); assert p.Path(f).read_bytes()==p.Path('restored').read_bytes()
  print(a,f,e,d,flush=True)
for f in ('note.txt','sample.bin'):
 for h in ('md5','sha1','sha256'): print(o('dgst','-'+h,f).strip())
 for alg in ('rsa','ec'):
  if alg=='rsa':
   opts=['-pkeyopt','rsa_padding_mode:oaep','-pkeyopt','rsa_oaep_md:sha256','-pkeyopt','rsa_mgf1_md:sha256']
   enc=lambda:o('pkeyutl','-encrypt','-pubin','-inkey','rsa-pub.pem',*opts,'-in',f,'-out','rsa.ct')
   dec=lambda:o('pkeyutl','-decrypt','-inkey','rsa.pem',*opts,'-in','rsa.ct','-out','restored')
  else:
   enc=lambda:o('cms','-encrypt','-binary','-aes-256-cbc','-in',f,'-outform','DER','-out','ec.ct','-recip','ec-cert.pem')
   dec=lambda:o('cms','-decrypt','-binary','-inform','DER','-in','ec.ct','-recip','ec-cert.pem','-inkey','ec.pem','-out','restored')
   o('req','-new','-x509','-key','ec.pem','-subj','/CN=ec.lab7.local','-days','30','-out','ec-cert.pem')
  times=[]
  for fn in (enc,dec):
   t=[]
   for _ in range(15):
    start=time.perf_counter(); fn();t.append((time.perf_counter()-start)*1000)
   times.append(round(st.median(t),3))
  assert p.Path(f).read_bytes()==p.Path('restored').read_bytes()
  print(alg,f,times,flush=True)

for algorithm in ('aes-256-cbc', 'des-cbc', 'chacha20'):
 print(o('speed', '-elapsed', '-seconds', '1', '-bytes', '16384',
         '-provider', 'default', '-provider', 'legacy', '-evp', algorithm))
print(o('speed', '-elapsed', '-seconds', '2', 'rsa2048'))

key = o('rand', '-hex', '32').strip()
iv = o('rand', '-hex', '16').strip()
for label, args in [
 ('AES-256-CBC', ['enc', '-aes-256-cbc', '-K', key, '-iv', iv]),
 ('RSA-OAEP', ['pkeyutl', '-encrypt', '-pubin', '-inkey', 'rsa-pub.pem', *opts]),
]:
 measurements = []
 for _ in range(31):
  start = time.perf_counter()
  o(*args, '-in', 'sample.bin', '-out', os.devnull)
  measurements.append((time.perf_counter() - start) * 1000)
 print(f'{label}: {st.median(measurements):.3f} ms (sample.bin)')
