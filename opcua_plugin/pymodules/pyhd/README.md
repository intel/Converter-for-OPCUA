# pyhd

## Description

pyhd plugin detects human in factory, cameras are installed in working floor and monitor the working environment. The videos are sent to edge gateway. The edge gateway conduct video analytics, when human appears in the forbidden area.

## Language

Python

## Configuration

The following properties can be configured by editing `plugin_pyhd.json`:

	id
		camera id, can be usb/network cameras
		
	width
		camera width
		
	height
		camera height
		
	period
		specify the period to detect

## Installs

Please follow the bellow steps to install ncsdk and opencv3.4.0 before runing the plugin

1. Install ncsdk and execute the webcam based person detection demo

1.1

	$ git clone https://github.com/movidius/ncsdk.git
	$ cd ncsdk
	$ vim ncsdk.conf

No need to install tensorflow, so set the tensorflow tool to "no" to prevent potential conflicts. We also suggests to not install the toolkit at this step.

	INSTALL_TENSORFLOW=no
	INSTALL_TOOLKIT=no

If you choose to install the toolkit in this step, then set ```INSTALL_TOOLKIT=yes```, and skip Step 1.2 and 1.3
Normally, it will fail with some of the packges

	$ sudo apt-get install python-pip
	$ sudo apt-get install python3-pip
	$ make install

It may take 10+ minutes in checking the previous installed NCSDK (Depends on your "opt" and "home" folder size)

1.2

Then install the toolkit manually according to ```/opt/movidius/NCSDK/requirements.txt```

For example:

	$ pip3 install -r /opt/movidius/NCSDK/requirements.txt

or

	$ pip3 install Pillow==4.2.1
	$ pip3 install PyYAML==3.12
	$ pip3 install PyYAML==3.12
  	...

If you have the issue "error: library dfftpack has Fortran sources but no Fortran compiler found" during install scipy, execute:

	$ sudo apt-get install liblapack-dev
	$ sudo apt-get install gfortran

1.3

If you don't have your caffe installed, install caffe according to the guide in [https://github.com/BVLC/caffe](https://github.com/BVLC/caffe)
The below two projects can also be used

* [https://github.com/weiliu89/caffe.git](https://github.com/weiliu89/caffe.git)
* [https://github.com/intel/caffe.git](https://github.com/intel/caffe.git)

Since we are using Movidius, we also tried SSD caffe, we guess this would be the best choice.

And add ```export PYTHONPATH="${PYTHONPATH}:/opt/movidius/caffe/python"``` to ```.bashrc```,
Then exec the following command to make sure the caffe has been installed correctly

	$ python3 -c "import caffe"

1.4

If everything works file, you can plugin the movidus dongle, then run the ncsdk native examples. These examples can detect the movidius sticks and give some outputs

	$ cd examples/caffe
	$ make

And you can also get other apps by using

	$ git clone https://github.com/movidius/ncappzoo.git

For example if you want to use SSD MobileNet

	$ cd ncappzoo/caffe/SSD_MobileNe
	$ make

1.5

Then we are going to run the YoloV2 to iamge and webcam

	$ git clone https://github.com/duangenquan/YoloV2NCS.git
	$ sudo apt-get install libopencv-dev python-opencv

We also need build and install latest opencv lib with webcam driver supported.
Here we are using the opencv3.4.0 and follow the steps below

	https://stackoverflow.com/questions/37188623/ubuntu-how-to-install-opencv-for-python3
	https://www.learnopencv.com/install-opencv3-on-ubuntu/

Please remove the WITH_TBB, WITH_V4L, WITH_OPENGL.
After the opencv3.4.0 has been built and install in the machine
Replace the detectionExample folder in the YoloV2 folder to the attached zip, then build

	$ make
	$ mvNCCompile ./models/caffemodels/yoloV2Tiny20.prototxt -w ./models/caffemodels/yoloV2Tiny20.caffemodel -s 12
	$ python3 ./detectionExample/Main.py --mthread 0

run the setup.sh to get the YoloV2NCS code
In linux OS, the ```/dev/video0``` mode is ```crw-rw----```, may need ```chmod to /dev/video0``` first

