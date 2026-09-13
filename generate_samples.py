"""Own fictional documents. None are real engineering specifications or test results."""
from pathlib import Path
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).parent/'sample_data'

def make_pdf(path,title,pages,model='BC-100',revision='B',version='1'):
    path.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(path),pagesize=(595,842),invariant=1)
    c.setTitle(title+' - SYNTHETIC DEMO')
    for n,lines in enumerate(pages,1):
        c.setFillColorRGB(.10,.18,.27);c.rect(0,750,595,92,fill=1,stroke=0)
        c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',17);c.drawString(40,799,title)
        c.setFont('Helvetica',10);c.drawString(40,775,'SYNTHETIC DEMO ONLY - NOT VALID FOR REAL MACHINERY')
        c.setFillColorRGB(.13,.16,.20);c.setFont('Helvetica',11)
        y=717
        for line in [f'Model: {model}',f'Design revision: {revision}',f'Document version: {version}','',*lines]:
            # Fixed short source lines preserve the demo's transparent mock parser.
            if len(line)>94:
                raise ValueError('Sample line too long: '+line)
            c.drawString(40,y,line);y-=23
        c.setFont('Helvetica',9);c.setFillColorRGB(.40,.45,.5)
        c.drawString(40,40,'Fictional university prototype; no actual test or safety conclusion.')
        c.drawRightString(555,40,f'Page {n} / {len(pages)}');c.showPage()
    c.save()

def main():
    make_pdf(ROOT/'BC100_Product_Spec.pdf','Product specification',[[
        'Manufacturer: Demo Conveyor Works, 1 Example Road, Seoul (fictional).',
        'Product identity: BC-100 standalone belt conveyor.',
        'Intended use: Move closed cartons horizontally in a dry indoor work area.',
        'Use limits: No people, hot materials or explosive atmospheres.',
        'These statements are fictional scenario data, not an approved design.']])
    make_pdf(ROOT/'BC100_User_Manual_v1.pdf','User manual',[[
        'Installation: Secure the base to the prepared floor using the supplied mounting points.',
        'Controls: Green START initiates motion; red STOP requests a normal stop.',
        'Residual risks: Keep loose clothing away from moving belt edges.'],[
        'Maintenance precautions: Isolate the power supply before inspection.',
        'The periodic service schedule has not yet been recorded.',
        'This manual is an incomplete fictional draft.']])
    make_pdf(ROOT/'BC90_Test_Report.pdf','Test record - illustrative',[[
        'Test scope: BC-90 revision B; unloaded indoor observation of start and stop behavior.',
        'Record identifier: DEMO-BC90-TR-01.',
        'No actual measured result is included. This is not a laboratory certificate.']],model='BC-90')
    make_pdf(ROOT/'BC100_Drawing_Summary.pdf','Drawing summary',[[
        'Drawing configuration: DR-BC100-A; legacy frame and guard arrangement.',
        'Guarding: A cover is illustrated over the drive area.',
        'The sketch description alone does not establish engineering sufficiency.']],revision='A')
    make_pdf(ROOT/'BC100_Revision_History.pdf','Revision history',[[
        'Revision history: Project baseline B replaces A; drawing A remains in the supplied folder.',
        'Manual v1 is associated with design baseline B.',
        'Document version numbers are separate from the design baseline.']])
    # Raster-only PDF deliberately exercises UNREADABLE; no false OCR claim.
    im=Image.new('RGB',(1080,1350),'white');d=ImageDraw.Draw(im)
    d.text((60,70),'SYNTHETIC DEMO ONLY - NOISE RECORD',fill='black',font=ImageFont.load_default(size=28))
    d.text((60,150),'This page is raster-only. No measured values are provided.',fill='black',font=ImageFont.load_default(size=24))
    d.text((60,210),'Request a readable source. Model and conditions need review.',fill='black',font=ImageFont.load_default(size=24))
    buff=BytesIO();im.save(buff,format='PNG');buff.seek(0)
    c=canvas.Canvas(str(ROOT/'BC100_Noise_Record.pdf'),pagesize=(595,842),invariant=1)
    c.drawImage(ImageReader(buff),0,0,width=595,height=842);c.showPage();c.save()
    make_pdf(ROOT/'revised/BC100_User_Manual_v2.pdf','User manual - revision 2',[[
        'Controls: Green START initiates motion; red STOP requests a normal stop.',
        'Residual risks: Keep loose clothing away from moving belt edges.',
        'Installation instructions are awaiting review and are omitted in this revision.'],[
        'Maintenance interval: Every 30 days (fictional value confirmed for this demo only).',
        'Maintenance precautions: Isolate the power supply before inspection.',
        'This revision intentionally loses installation detail to test re-opening.']],version='2')
    make_pdf(ROOT/'revised/BC100_Drawing_Summary_v2.pdf','Drawing summary - revision 2',[[
        'Drawing configuration: DR-BC100-B; updated frame and guard arrangement.',
        'Guarding: A cover is illustrated over the drive area.',
        'Engineering sufficiency still requires a qualified reviewer.']],version='2')
    print('Generated 6 initial + 2 revised synthetic PDFs.')

if __name__=='__main__':main()
