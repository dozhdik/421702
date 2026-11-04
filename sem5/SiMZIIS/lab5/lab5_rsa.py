#!/usr/bin/env python3
import argparse
import base64
import csv
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import secrets
import time

H = hashlib.sha256
HLEN = 32

def mod_pow(base, exponent, modulus):
    if exponent < 0 or modulus <= 0:
        raise ValueError('Недопустимые показатель или модуль')
    result, base = 1 % modulus, base % modulus
    while exponent:
        if exponent & 1:
            result = result * base % modulus
        base = base * base % modulus
        exponent >>= 1
    return result

def inverse(a, modulus):
    old_r, r, old_s, s = a, modulus, 1, 0
    while r:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
    if old_r != 1:
        raise ValueError('Обратное число не существует')
    return old_s % modulus

def is_probable_prime(n, rounds=64):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(rounds):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True

def prime(bits, e=65537):
    while True:
        p = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if math.gcd(e, p - 1) == 1 and is_probable_prime(p):
            return p

def keygen(bits=1024):
    if bits < 1024:
        raise ValueError('По методичке p и q должны иметь не менее 1024 бит')
    e = 65537
    while True:
        p, q = prime(bits), prime(bits)
        n = p * q
        if p != q and n.bit_length() == 2 * bits:
            break
    phi = (p - 1) * (q - 1)
    return dict(n=n, e=e, d=inverse(e, phi), p=p, q=q)

def save_key(path, key, private=False):
    fields = ('n', 'e', 'd', 'p', 'q') if private else ('n', 'e')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600 if private else 0o644)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump({'format': 'RSA-LAB-1', **{k: str(key[k]) for k in fields}}, f, indent=2)

def load_key(path, private=False):
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    if obj.get('format') != 'RSA-LAB-1':
        raise ValueError('Неизвестный формат ключа')
    fields = ('n', 'e', 'd', 'p', 'q') if private else ('n', 'e')
    key = {k: int(obj[k]) for k in fields}
    if key['n'].bit_length() < 2048 or not 1 < key['e'] < key['n'] or key['e'] % 2 == 0:
        raise ValueError('Недопустимый открытый ключ')
    if private:
        p, q = key['p'], key['q']
        if min(p.bit_length(), q.bit_length()) < 1024 or p == q or p*q != key['n']:
            raise ValueError('Недопустимые p и q')
        if key['d'] <= 0 or key['e']*key['d'] % ((p-1)*(q-1)) != 1:
            raise ValueError('Недопустимая закрытая экспонента')
    return key

def xor(a, b):
    if len(a) != len(b):
        raise ValueError('Различные длины XOR')
    return bytes(x ^ y for x, y in zip(a, b))

def mgf1(seed, length):
    return b''.join(H(seed + i.to_bytes(4, 'big')).digest()
                    for i in range((length + HLEN - 1)//HLEN))[:length]

def oaep_encode(message, k):
    if len(message) > k - 2*HLEN - 2:
        raise ValueError('Слишком длинный OAEP-блок')
    db = H(b'').digest() + b'\0'*(k-len(message)-2*HLEN-2) + b'\1' + message
    seed = secrets.token_bytes(HLEN)
    masked_db = xor(db, mgf1(seed, k-HLEN-1))
    return b'\0' + xor(seed, mgf1(masked_db, HLEN)) + masked_db

def oaep_decode(encoded):
    if len(encoded) < 2*HLEN+2 or encoded[0] != 0:
        raise ValueError('Некорректный OAEP-блок')
    masked_seed, masked_db = encoded[1:HLEN+1], encoded[HLEN+1:]
    seed = xor(masked_seed, mgf1(masked_db, HLEN))
    db = xor(masked_db, mgf1(seed, len(masked_db)))
    if not hmac.compare_digest(db[:HLEN], H(b'').digest()):
        raise ValueError('Некорректный OAEP-блок')
    pos = HLEN
    while pos < len(db) and db[pos] == 0:
        pos += 1
    if pos == len(db) or db[pos] != 1:
        raise ValueError('Некорректный OAEP-блок')
    return db[pos+1:]

def encrypt(data, key):
    n, e = key['n'], key['e']
    k = (n.bit_length()+7)//8
    chunk = k - 2*HLEN - 2
    blocks = []
    for start in range(0, max(1, len(data)), chunk):
        m = int.from_bytes(oaep_encode(data[start:start+chunk], k), 'big')
        blocks.append(base64.b64encode(mod_pow(m,e,n).to_bytes(k,'big')).decode())
    return {'format':'RSA-OAEP-SHA256-LAB-1', 'size':len(data), 'blocks':blocks}

def decrypt(envelope, key):
    if envelope.get('format') != 'RSA-OAEP-SHA256-LAB-1':
        raise ValueError('Неизвестный формат шифртекста')
    size, blocks = envelope.get('size'), envelope.get('blocks')
    n, d = key['n'], key['d']
    k = (n.bit_length()+7)//8
    chunk = k-2*HLEN-2
    if type(size) is not int or size < 0 or not isinstance(blocks,list):
        raise ValueError('Некорректная длина')
    if len(blocks) != max(1,(size+chunk-1)//chunk):
        raise ValueError('Некорректное число блоков')
    decoded = []
    for index, block in enumerate(blocks):
        raw = base64.b64decode(block, validate=True)
        c = int.from_bytes(raw,'big')
        if len(raw) != k or c >= n:
            raise ValueError('Некорректный RSA-блок')
        message = oaep_decode(mod_pow(c,d,n).to_bytes(k,'big'))
        expected = chunk if index < len(blocks)-1 else size-chunk*index
        if len(message) != expected:
            raise ValueError('Некорректная длина блока')
        decoded.append(message)
    return b''.join(decoded)

def pss_encode(data, em_bits):
    em_len = (em_bits+7)//8
    salt = secrets.token_bytes(HLEN)
    digest = H(b'\0'*8 + H(data).digest() + salt).digest()
    db = b'\0'*(em_len-2*HLEN-2) + b'\1' + salt
    masked = bytearray(xor(db,mgf1(digest,len(db))))
    masked[0] &= 0xff >> (8*em_len-em_bits)
    return bytes(masked)+digest+b'\xbc'

def sign(data, key):
    n = key['n']; k = (n.bit_length()+7)//8
    m = int.from_bytes(pss_encode(data,n.bit_length()-1),'big')
    return mod_pow(m,key['d'],n).to_bytes(k,'big')

def verify(data, signature, key):
    n = key['n']; k = (n.bit_length()+7)//8
    if len(signature) != k or int.from_bytes(signature,'big') >= n:
        return False
    em_bits = n.bit_length()-1; em_len = (em_bits+7)//8
    value = mod_pow(int.from_bytes(signature,'big'),key['e'],n)
    if value >= 1 << (8*em_len):
        return False
    em = value.to_bytes(em_len,'big')
    if em[-1] != 0xbc or em_len < 2*HLEN+2:
        return False
    masked, digest = em[:-HLEN-1], em[-HLEN-1:-1]
    unused = 8*em_len-em_bits
    if masked[0] & (0xff ^ (0xff >> unused)):
        return False
    db = bytearray(xor(masked,mgf1(digest,len(masked))))
    db[0] &= 0xff >> unused
    if bytes(db[:-HLEN]) != b'\0'*(em_len-2*HLEN-2)+b'\1':
        return False
    expected = H(b'\0'*8 + H(data).digest() + bytes(db[-HLEN:])).digest()
    return hmac.compare_digest(digest,expected)

def write_json(path, obj):
    path = Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def selftest(folder):
    root = Path(folder); root.mkdir(parents=True,exist_ok=True)
    fixtures = [b'',b'A',b'\0', 'Вариант 9: RSA и цифровая подпись'.encode(),
                bytes(range(256)), b'X'*189,b'X'*190,b'X'*191,
                ('Строка с ё, Ё и emoji 🔐\n'*20).encode(),secrets.token_bytes(1024)]
    rows = []
    for i,data in enumerate(fixtures,1):
        case = root/f'case_{i:02d}'; case.mkdir(exist_ok=True)
        t = time.perf_counter(); key = keygen(); key_s = time.perf_counter()-t
        save_key(case/'public_key.json',key); save_key(case/'private_key.json',key,True)
        (case/'message.bin').write_bytes(data)
        pub=load_key(case/'public_key.json'); prv=load_key(case/'private_key.json',True)
        t=time.perf_counter(); env=encrypt(data,pub); enc_s=time.perf_counter()-t
        write_json(case/'ciphertext.json',env)
        t=time.perf_counter(); restored=decrypt(json.loads((case/'ciphertext.json').read_text()),prv); dec_s=time.perf_counter()-t
        (case/'restored.bin').write_bytes(restored)
        t=time.perf_counter(); signature=sign(data,prv); sign_s=time.perf_counter()-t
        (case/'signature.bin').write_bytes(signature)
        t=time.perf_counter(); good=verify(data,signature,pub); verify_s=time.perf_counter()-t
        altered=not verify(data+b'!',signature,pub)
        bad=bytearray(signature); bad[-1]^=1
        bad_sig=not verify(data,bytes(bad),pub)
        damaged=dict(env); damaged['blocks']=list(env['blocks'])
        raw=bytearray(base64.b64decode(damaged['blocks'][0])); raw[-1]^=1
        damaged['blocks'][0]=base64.b64encode(raw).decode()
        try:
            decrypt(damaged,prv); damaged_rejected=False
        except ValueError:
            damaged_rejected=True
        if not (restored==data and good and altered and bad_sig and damaged_rejected):
            raise AssertionError(f'Набор {i} не прошёл')
        row=dict(case=i,bytes=len(data),p_bits=key['p'].bit_length(),q_bits=key['q'].bit_length(),
                 n_bits=key['n'].bit_length(),blocks=len(env['blocks']),key_s=key_s,encrypt_s=enc_s,
                 decrypt_s=dec_s,sign_s=sign_s,verify_s=verify_s,roundtrip=True,signature=True,
                 modified_message_rejected=altered,modified_signature_rejected=bad_sig,
                 modified_ciphertext_rejected=damaged_rejected,sha256=H(data).hexdigest())
        rows.append(row); write_json(case/'result.json',row)
        print(f'{i:02d}: {len(data)} байт; p/q={row["p_bits"]}/{row["q_bits"]}; PASS',flush=True)
    with (root/'summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    write_json(root/'summary.json',rows)

def main():
    parser=argparse.ArgumentParser(description='ЛР5, вариант 9. RSA: собственные Miller–Rabin, Евклид, square-and-multiply,\nOAEP/SHA-256 и PSS/SHA-256. Python 3.10+, только стандартная библиотека.\nУчебная реализация: не constant-time; закрытые ключи в JSON без пароля.\nФайлы шифртекста содержат независимые OAEP-блоки; целостность всего файла\nподтверждается отдельной PSS-подписью исходного файла.\n')
    sub=parser.add_subparsers(dest='command',required=True)
    g=sub.add_parser('keygen');g.add_argument('--bits',type=int,default=1024);g.add_argument('--out',default='results/lab5/keys')
    for cmd in ('encrypt','decrypt','sign','verify'):
        p=sub.add_parser(cmd);p.add_argument('--key',required=True);p.add_argument('--input',required=True)
        p.add_argument('--signature',required=True) if cmd=='verify' else p.add_argument('--output',required=True)
    t=sub.add_parser('selftest');t.add_argument('--out',default='results/lab5')
    args=parser.parse_args()
    try:
        if args.command=='keygen':
            key=keygen(args.bits);save_key(Path(args.out)/'public_key.json',key);save_key(Path(args.out)/'private_key.json',key,True)
            print(f'Сохранены ключи, n={key["n"].bit_length()} бит')
        elif args.command=='selftest': selftest(args.out)
        else:
            key=load_key(args.key,args.command in ('decrypt','sign')); data=Path(args.input).read_bytes()
            if args.command=='encrypt': write_json(args.output,encrypt(data,key))
            elif args.command=='decrypt': Path(args.output).write_bytes(decrypt(json.loads(data),key))
            elif args.command=='sign': Path(args.output).write_bytes(sign(data,key))
            else:
                valid=verify(data,Path(args.signature).read_bytes(),key)
                print('Подпись верна' if valid else 'Подпись неверна')
                return 0 if valid else 1
    except (ValueError,KeyError,TypeError,OSError) as exc:
        parser.exit(2,f'Ошибка: {exc}\n')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
