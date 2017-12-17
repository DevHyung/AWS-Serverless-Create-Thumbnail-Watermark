import boto3
import uuid
from PIL import Image

s3_client = boto3.client('s3')
def resize_image(target, image_path, wimage_path, resizetype, rwidth=0, rheight=0, ext=[], wposition="center",
                  wsize=1.0):
    with Image.open(image_path) as image:
        imgwidth, imgheight = image.size
        if resizetype == "max":
            if rwidth > rheight:  # width grater
                rheight = rwidth
            else:  # height grater
                rwidth = rheight
            image.thumbnail((rwidth, rheight), Image.ANTIALIAS)
        else:  # resizetype fit
            ratio = min(imgwidth, imgheight) / float(max(imgwidth, imgheight))
            if rwidth == 0:
                rwidth = int(rheight * ratio)
            if rheight == 0:
                rheight = int(rwidth * ratio)
            image = image.resize((rwidth, rheight))
        print("Success : Image resize")
        create_watermarkimg(image, wimage_path, target, wposition, wsize, ext)
def create_watermarkimg(image, waterimage_path, target, position, size, ext):
    with Image.open(waterimage_path) as wimage:
        width, height = image.size
        wwidth, wheight = wimage.size
        if width > height:
            wwidth = int(width * size)
            wheight = wwidth
        else:
            wheight = int(height * size)
            wwidth = wheight
        wimage.thumbnail((wwidth, wheight), Image.ANTIALIAS)
        wwidth, wheight = wimage.size
        posx, posy = 0, 0  # init
        position = str(position).replace(" ", "")
        posilist = position.split("|")
        for posi in posilist:
            if posi == "center":
                posx = (width - wwidth) / 2
                posy = (height - wheight) / 2
            if posi == "left":
                posx = 0
            if posi == "right":
                posx = width - wwidth
            if posi == "top":
                posy = 0
            if posi == "bottom":
                posy = height - wheight
        image.paste(wimage, (posx, posy), wimage)
        print("Success : Image paste watermark")
        tmptarget = str(target).split(".")[0] + "."
        print(tmptarget)
        for saveext in ext:
            print("Success : save image " + saveext + " extention ")
            image.save(tmptarget + saveext)
def getimagesizetag(imagepath):
    with Image.open(imagepath) as image:
        width, height = image.size
        tag = "(" + str(width) + "X" + str(height) + ")"
        return tag
def handler(event, context):
    for record in event['Records']:
        try:
            # json parsing and download S3 source bucket
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            download_path = '/tmp/{}{}'.format(uuid.uuid4(), key)
            upload_path = '/tmp/resized-{}'.format(key)
            s3_client.download_file(bucket, key, download_path)

            # customized JSON HERE
            watermark_file = 'watermark.png'
            watermark_position = 'bottom|left'
            watermark_size = 0.5
            resize_type = 'max'
            width = 512 # if width size null input 0
            height = 512
            ext = ["jpg", "png"]
            save_target = "thumb/" # this code bucket/thumb  folder auto making
            # function call
            resize_image(upload_path, download_path, watermark_file, resize_type, width, height, ext, watermark_position, watermark_size)
            try:
                bucketname = str(bucket).split("-")[0]
                tmp_path = str(upload_path).split(".")[0] + "."
                tmp_key = str(key).split(".")[0] + "."
                s3_client.delete_object(Bucket=bucketname + '-source-img', Key=key)
                print("Success : Delete source Bucket")
                # origin image save
                s3_client.upload_file(download_path, '{}-origin-img'.format(bucketname), getimagesizetag(download_path) + key)
                # upload by ext list example ["jpg","png"]
                for saveext in ext:
                    upload_path = tmp_path + saveext
                    s3_client.upload_file(upload_path, '{}-demand-img'.format(bucketname), save_target + getimagesizetag(upload_path) + tmp_key + saveext)
                    print ("Success : upload image " + saveext + " format in demand bucket")
            except:
                print("Error 1 : upload fail origin, demand if do not display delete message, delete error")
        except:
            print("Error 0 : Download fail check the bucket permission ")
            s3_client.upload_file(download_path, '{}-error-img'.format(bucketname), key)

