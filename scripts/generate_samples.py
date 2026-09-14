"""Generate real synthetic documents for the upload demonstration."""
from pathlib import Path
from email.message import EmailMessage
from openpyxl import Workbook
from reportlab.pdfgen import canvas

root=Path(__file__).resolve().parents[1]/'projects'/'remittance'/'sample-data'
root.mkdir(parents=True,exist_ok=True)
fields={'Customer':'Northline Studio','Invoice':'INV-1004','Amount':'640.00','Reference':'BANK-UPLOAD-001','Currency':'USD'}
text='\n'.join(f'{k}: {v}' for k,v in fields.items())
(root/'remittance.txt').write_text(text,encoding='utf-8')
c=canvas.Canvas(str(root/'remittance.pdf'));c.setTitle('Synthetic remittance advice')
c.setFont('Helvetica-Bold',22);c.drawString(48,785,'Remittance advice')
c.setFont('Helvetica',10);c.drawString(48,761,'SYNTHETIC PORTFOLIO FIXTURE - NO REAL PAYMENT')
for i,line in enumerate(text.splitlines()):c.drawString(48,710-i*26,line)
c.drawString(48,480,'Prepared to demonstrate document extraction and invoice matching.');c.save()
wb=Workbook();ws=wb.active;ws.title='Remittance';ws.append(list(fields));ws.append(list(fields.values()));wb.save(root/'remittance.xlsx')
(root/'remittance.csv').write_text(','.join(fields)+'\n'+','.join(fields.values())+'\n',encoding='utf-8')
msg=EmailMessage();msg['From']='payments@example.test';msg['To']='receivables@example.test';msg['Subject']='Synthetic remittance - INV-1004';msg.set_content('Please find the synthetic remittance attached.')
msg.add_attachment((root/'remittance.pdf').read_bytes(),maintype='application',subtype='pdf',filename='remittance.pdf')
(root/'remittance.eml').write_bytes(msg.as_bytes())
print(f'Generated 5 synthetic sample files in {root}')
