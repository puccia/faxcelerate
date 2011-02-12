import os, sys
from datetime import datetime

def set_environment():
	import os, sys
	sys.path.append(os.path.dirname(__file__) + '/../..')
	dsm = 'DJANGO_SETTINGS_MODULE'
	if dsm not in os.environ.keys():
		os.environ[dsm] = 'faxcelerate.settings'

set_environment()

from faxcelerate import settings
from faxcelerate.fax.models import Fax

TIFF_OUTPUT_DIR = os.path.join(settings.FAX_SPOOL_DIR, 'senttiff')



if __name__ == '__main__':
    qfile, why = sys.argv[1:3]
    print qfile, why
    # Exit if fax is still in queue.
    # Continue if fax is done or aborted due to an error
    if why in ('blocked', 'requeued'):
        sys.exit(1)

    # Scan qfile for info
    info = {}
    for line in open(os.path.join(settings.FAX_SPOOL_DIR, qfile), 'r'):
        tag, data = line.split(':', 1)
	data = data.strip()
        if tag[0] == '!':
            if not tag in info:
                info[tag] = []
            info[tag].append(data)
        else:
            info[tag] = data
    print info

    # Exit if job is not done
    if info['state'] != '7':
        sys.exit(1)

    error_message = None
    if why != 'done':
        try:
            error_message = '%s: %s' % (why, info['status'])
        except KeyError:
            error_message = why
    print 'OK'

    # Build TIFF file
    input_files = [os.path.join(settings.FAX_SPOOL_DIR, name.split(':')[-1])
        for name in info['!postscript']]
    output_file = '%s.tif' % os.path.join(TIFF_OUTPUT_DIR, info['commid'])
    os.system('gs -dBATCH -dNOPAUSE -q -sDEVICE=tiffg3 -sOutputFile=%s %s -r200'
        % (output_file, ' '.join(input_files)))
    
    # Store in DB
    fax = Fax()
    fax.comm_id = info['commid']
    fax.filename = 'senttiff/%s.tif' % info['commid']
    fax.local_sender = '%s@%s' % (info['mailaddr'], info['client'])
    fax.caller_id = info['number']
    fax.received_on = datetime.fromtimestamp(float(info['tts']))
    fax.time_to_receive = 1
    fax.outbound = True
    fax.update_from_tiff()
    if error_message:
        fax.reason = error_message
    fax.save()
    from faxcelerate.fax.image import FaxImage
    FaxImage(fax).cache_thumbnails()
	
    
