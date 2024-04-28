# FIA-
A secure and cardless security for ATMs
#Prerequistes
sudo pip3 install adafruit-circuitpython-fingerprint pyfingerprint

git clone https://github.com/adafruit/Adafruit_CircuitPython_Fingerprint.git

git clone https://github.com/bastianraschke/pyfingerprint.git

Install face_recognition module and other required modules imported in the code.
Hardware requirements 
1.Raspberry pi
2.picam4
3.R307 fingerprint sensor 
Refer materials to connect the hardware.
#Steps to run the face training 
1. first create a directory named Face Recognition 
2. save the files face_shot.py , face_rec.py, train_model.py and also save the .xml file which contains the pretrained model of face
3. create another directory inside this directory named datasets.
4. create directory with name of the person as label inside the dataset directory.
5. Then run the code files_shot.py and capture as many faces with different positions.
6. run the file train_model by replacing the file name with the label you given to the directory inside the datasets.
#Steps to add user
1. Run the file admin.py
2. Then a interface will come.
3. Add the user details
#Steps to manage fingerprint
1. Run the file named with fingerprint_simplest_rpi.py
Steps to get the FIA atm interface
1. Run the file face_rec.py
