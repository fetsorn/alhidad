#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Generate graph/assets.ttl from data-file.csv and content metadata.

One :Data node per unique content hash.
Attributes of the content: filesize, mediaType, filetype.
"""

import mimetypes
import sys
from collections import defaultdict
from lib import GRAPH_DIR, PREFIXES, escape_turtle, read_csv


def main():
    print("=== gen-assets: reading data-file.csv ===", file=sys.stderr)
    hash_paths = defaultdict(list)
    count = 0
    for h, p in read_csv("data-file.csv"):
        hash_paths[h].append(p)
        count += 1
        if count % 100000 == 0:
            print(f"  {count} path entries...", file=sys.stderr)
    print(f"  {count} paths, {len(hash_paths)} unique hashes", file=sys.stderr)

    # Content-keyed metadata (hash -> value)
    print("  reading content metadata...", file=sys.stderr)
    hash_filesize = dict(read_csv("data-filesize.csv"))
    hash_filetype = dict(read_csv("data-filetype.csv"))
    print(f"  filesizes: {len(hash_filesize)}, filetypes: {len(hash_filetype)}", file=sys.stderr)

    # Write TTL
    out = GRAPH_DIR / "assets.ttl"
    print(f"  writing {out}...", file=sys.stderr)
    emitted = 0
    total = len(hash_paths)
    with open(out, "w", encoding="utf-8") as f:
        f.write(PREFIXES)
        for h, paths in hash_paths.items():
            iri = f"<urn:sha256:{h}>"
            f.write(f"{iri} a :Data")

            # mediaType from extension (use first path)
            mt = mimetypes.guess_type(paths[0])[0]
            if mt:
                f.write(f' ;\n  :mediaType "{mt}"')

            if h in hash_filesize:
                f.write(f' ;\n  :filesize "{escape_turtle(hash_filesize[h])}"')
            if h in hash_filetype:
                f.write(f' ;\n  :filetype "{escape_turtle(hash_filetype[h])}"')

            f.write(" .\n")
            emitted += 1
            if emitted % 50000 == 0:
                print(f"  {emitted}/{total} assets...", file=sys.stderr)

    print(f"  wrote {out} ({emitted} assets)", file=sys.stderr)


if __name__ == "__main__":
    main()
