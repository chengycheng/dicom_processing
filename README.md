# dicom_processing
Simple flask application to manipulate DICOM format imaging files

## Starting the microservice
python micro_service.py

## Sample calls
### Upload File 
from terminal: ```curl -X POST -F 'file=@IM000003' http://127.0.0.1:5000/upload```

### Search by Tag:
```http://127.0.0.1:5000/header/IM000001?tag=(0028,0004)```

### Convert to Image
```http://127.0.0.1:5000/convert/IM000001```


References:
- I referenced [here](https://stackoverflow.com/questions/74027712/converting-hand-radiograph-dicom-to-png-returns-white-bright-image) to troubleshoot with IM000003 turning out all white after conversion.
