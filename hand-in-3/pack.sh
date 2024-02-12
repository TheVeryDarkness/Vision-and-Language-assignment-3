set -eux

OUT="hand-in-3"

if [ -d "$OUT" ]; then
    rm -r "$OUT"
fi

mkdir "$OUT"

cp *.png "$OUT"
cp *.html "$OUT"

cp hand-in.md "$OUT"
cp generate.py "$OUT"
cp show.py "$OUT"
cp pack.sh "$OUT"

zip "$OUT.zip" -r "$OUT"
