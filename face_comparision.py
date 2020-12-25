import boto3
from PIL import Image
import base64


def compare_faces(sourceFile, targetFile, date):
    client = boto3.client('rekognition')
    imageSource = open(sourceFile, 'rb')
    imageTarget = open(targetFile, 'rb')
    response = client.compare_faces(SimilarityThreshold=80,
                                    SourceImage={'Bytes': imageSource.read()},
                                    TargetImage={'Bytes': imageTarget.read()})

    stat = False
    cpdb64 = ""
    if len(response['FaceMatches']) > 0:
        jj = response['FaceMatches'][0]["Face"]["BoundingBox"]
        img = Image.open(targetFile)
        imgWidth, imgHeight = img.size
        left = imgWidth * jj["Left"]
        top = imgHeight * jj["Top"]
        width = imgWidth * jj["Width"]
        height = imgHeight * jj["Height"]
        crpd = img.crop((left, top, left + width, top + height))
        path = "./uploaded_images/detected/"+date+".jpg"
        crpd.save(path)
        with open(path, "rb") as image_file:
            cpdb64 = base64.b64encode(image_file.read())
            cpdb64 = cpdb64.decode('utf-8')
        stat = True
    # jj = []
    # i = 1
    # for faceMatch in response['FaceMatches']:
    #     position = faceMatch['Face']['BoundingBox']
    #     similarity = str(faceMatch['Similarity'])
    #     mm = {i: 'The face at ' + str(position['Left']) + ' ' + str(
    #         position['Top']) + ' matches with ' + similarity + '% confidence '}
    #     jj.append(mm)
    #     i = i + 1

    imageSource.close()
    imageTarget.close()
    return {"cropped": cpdb64, "status": stat}


def main(source_file, target_file, date):
    # source_file = 'uploaded_images/source/gutta.jpg'
    # target_file = 'uploaded_images/daily_tmp/group.jpg'
    face_matches = compare_faces(source_file, target_file, date)
    # msg = {"Face matches": face_matches}
    return face_matches


if __name__ == "__main__":
    main()
