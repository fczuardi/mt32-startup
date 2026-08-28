from pathlib import Path
import struct


def presets(path):
    data = Path(path).read_bytes()
    phdr = chunk(riff_list(data, b"pdta"), b"phdr")
    out = []
    for offset in range(0, len(phdr) - 38, 38):
        record = phdr[offset:offset + 38]
        name = record[:20].split(b"\0", 1)[0].decode("latin1")
        program, bank = struct.unpack_from("<HH", record, 20)
        if name != "EOP" and bank <= 128 and program <= 127:
            out.append((bank, program, name))
    return sorted(out)


def preset_map(path):
    return {(bank, program): name for bank, program, name in presets(path)}


def riff_list(data, kind):
    for chunk_id, body in chunks(data[12:]):
        if chunk_id == b"LIST" and body[:4] == kind:
            return body[4:]
    raise ValueError(f"could not find {kind.decode()} list")


def chunk(data, wanted):
    for chunk_id, body in chunks(data):
        if chunk_id == wanted:
            return body
    raise ValueError(f"could not find {wanted.decode()} chunk")


def chunks(data):
    offset = 0
    while offset + 8 <= len(data):
        chunk_id = data[offset:offset + 4]
        size = struct.unpack_from("<I", data, offset + 4)[0]
        start = offset + 8
        yield chunk_id, data[start:start + size]
        offset = start + size + (size % 2)
