"""Create captioned walkthroughs from real app screenshots. Requires FFmpeg."""
from pathlib import Path
import subprocess
import json
import shutil
import os

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent.parent/'work'/'media'
WORK.mkdir(parents=True,exist_ok=True)
scenes={
 'remittance':[
  ('01-dashboard.png','LedgerFlow | 10 synthetic documents: 2 posted, 7 held, 1 duplicate blocked.'),
  ('02-exception.png','A partial payment is held for review. Inspect the source and invoice balance.'),
  ('03-resolved.png','A reviewer verifies USD 300, records evidence and posts the partial payment.'),
  ('04-architecture.png','Parsing, deterministic validation, human review and durable audit history.')],
 'leads':[
  ('01-dashboard.png','FieldFlow | From service inquiry to quote, booking and customer follow-up.'),
  ('02-intake.png','A synthetic move-out inquiry enters one CRM workflow.'),
  ('03-calendar-conflict.png','After quote approval, the occupied calendar slot is blocked.'),
  ('04-booked.png','An available slot is booked. Calendar and confirmation receipts are recorded.'),
  ('05-architecture.png','Lifecycle rules cover reminders, no-response recovery and consent-based reactivation.')],
 'guests':[
  ('01-dashboard.png','StayOps | Approved answers are scoped to the correct property and reservation.'),
  ('02-emergency.png','A smoke report triggers an urgent host alert and immediate safe standby response.'),
  ('03-knowledge-approval.png','An unknown question becomes a proposed knowledge entry after a human answer.'),
  ('04-learned-answer.png','Only after separate approval can the next matching question be answered automatically.'),
  ('05-architecture.png','Global policy, property knowledge and review gates remain explicit.')],
 'orders':[
  ('01-dashboard.png','TradeFlow | Coordinate orders, inventory, fulfillment, invoices and payments.'),
  ('02-retry-scheduled.png','A supplier request fails. The same order key is retained for a safe retry.'),
  ('03-escalation.png','Three failed attempts open a critical exception for human review.'),
  ('04-recovered.png','An approver verifies recovery. Attempt four dispatches the original order once.'),
  ('05-reconciled.png','Finance reconciles the USD 2,240 payment with the invoice and completes the order.'),
  ('06-architecture.png','Durable state, bounded retries, role gates, exception deadlines and audit receipts.')]
}
for project,shots in scenes.items():
    stage=WORK/project;stage.mkdir(exist_ok=True)
    font=Path('C:/Windows/Fonts/arial.ttf') if os.name=='nt' else Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    shutil.copyfile(font,stage/'font.ttf')
    clips=[]
    for index,(filename,caption) in enumerate(shots):
        cap=stage/f'caption-{index}.txt';cap.write_text(caption,encoding='utf-8')
        clip=stage/f'{index:02}.mp4';clips.append(clip)
        vf=f"scale=1920:960:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:0:color=0x132e32,drawtext=font=Arial:textfile=caption-{index}.txt:fontcolor=white:fontsize=27:x=(w-tw)/2:y=995,drawtext=font=Arial:text='SYNTHETIC DEMO  |  SIMULATED PROVIDERS  |  ACTUAL APP CAPTURES':fontcolor=0xa7c4c0:fontsize=17:x=(w-tw)/2:y=1040"
        vf='crop=iw:min(ih\\,1080):0:0,'+vf.replace('font=Arial','fontfile=font.ttf')
        subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(ROOT/'projects'/project/'assets'/filename),'-vf',vf,'-t','12','-r','12','-c:v','libx264','-preset','fast','-crf','24','-pix_fmt','yuv420p',str(clip)],cwd=stage,check=True)
    concat=stage/'clips.txt';concat.write_text('\n'.join(f"file '{p.name}'" for p in clips),encoding='utf-8')
    target=ROOT/'projects'/project/'assets'/'walkthrough.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(target)],check=True)
    (ROOT/'projects'/project/'assets'/'video-notes.txt').write_text('Captioned walkthrough from actual application screenshots. Not a continuous screen recording.\nDuration: '+str(len(shots)*12)+' seconds. No audio. Synthetic inputs and simulated external providers.\n',encoding='utf-8')
    print(f'{project}: {target.name}, {len(shots)*12}s, {target.stat().st_size:,} bytes',flush=True)
