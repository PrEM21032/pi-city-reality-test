from kokoro_onnx import Kokoro
import soundfile as sf, json
k=Kokoro("/tmp/claude-0/voices/kokoro-v1.0.onnx","/tmp/claude-0/voices/voices-v1.0.bin")
# (start_sec, window_end, text). "Pie Station O S" is a phonetic spelling of "PI StationOS".
LINES=[
 (1.2, 14.5, "Six A M, on the Bayou La Batre Highway. The pumps are busy. The coolers are running low. The line at the register keeps growing. And every number in this store needs your attention."),
 (16.0, 29.5, "Meet Pie Station O S. An A I operations manager, built to watch the details of one gas station, so you never have to watch them alone."),
 (31.0, 49.5, "Pie reads your product sales, item by item. It spots what's selling faster than usual, predicts shortages before the shelf goes empty, and prepares the supplier order, ready for your review."),
 (51.0, 69.5, "It tracks fuel sales by grade. It reconciles the cash drawer against expected totals, and flags any variance. And it keeps every shift's task list moving."),
 (71.0, 89.5, "Then, it brings it all to you. From your phone, see what Pie found, and why it matters. Approve, edit, or decline each recommendation, with a single tap."),
 (91.0, 104.5, "Approved actions run as automated workflows. Every result is verified, and logged. Nothing happens without your approval. You stay in control."),
 (106.5, 118.5, "Pie Station O S. One store. A thirty day pilot. See what your station can do."),
]
meta=[]
for i,(st,en,txt) in enumerate(LINES):
    speed=0.92
    while True:
        s,sr=k.create(txt,voice="am_michael",speed=speed,lang="en-us")
        d=len(s)/sr
        if st+d<=en or speed>1.15: break
        speed+=0.03
    sf.write(f"vo_{i}.wav",s,sr); meta.append(dict(i=i,start=st,dur=d,speed=speed,text=txt))
    print(i,st,round(d,2),round(st+d,2),en,speed)
json.dump(meta,open("vo.json","w"),indent=1)
