import struct, zlib, os

def create_png(size, color=(34, 197, 94)):
    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    
    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
    
    raw = b''
    for y in range(size):
        raw += b'\x00'
        for x in range(size):
            raw += bytes(color)
    
    idat = chunk(b'IDAT', zlib.compress(raw))
    iend = chunk(b'IEND', b'')
    
    return header + ihdr + idat + iend

icons_dir = os.path.expanduser('~/hermes-browser-bridge/extension/icons')
os.makedirs(icons_dir, exist_ok=True)

for s in [16, 48, 128]:
    path = os.path.join(icons_dir, f'icon{s}.png')
    with open(path, 'wb') as f:
        f.write(create_png(s))
    print(f'icon{s}.png ({os.path.getsize(path)} bytes)')
