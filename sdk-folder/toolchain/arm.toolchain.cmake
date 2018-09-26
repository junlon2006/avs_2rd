# this is required
SET(CMAKE_SYSTEM_NAME Linux)

# specify the cross compiler
#SET(CMAKE_C_COMPILER   /opt/gcc-arm-none-eabi-7-2018-q2-update/bin/arm-none-eabi-gcc)
#SET(CMAKE_CXX_COMPILER /opt/gcc-arm-none-eabi-7-2018-q2-update/bin/arm-none-eabi-g++)

SET(CMAKE_C_COMPILER    arm-linux-gnueabihf-gcc-5)
SET(CMAKE_CXX_COMPILER  arm-linux-gnueabihf-g++-5)

SET(CMAKE_CXX_FLAGS  "-std=c++11 -fPIC")

# where is the target environment
SET(CMAKE_FIND_ROOT_PATH /home/junlon2006/workspace/amazon/avs_2rd/sdk-folder/third-party/ /usr/arm-linux-gnueabi/)

# search for programs in the build host directories (not necessary)
#SET(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
# for libraries and headers in the target directories
SET(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
SET(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)