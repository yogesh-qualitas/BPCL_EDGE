import threading
import time
from ImageConvert import *
from MVSDK import *
import numpy 

class DahuaCameras:
    def __init__(self, id, pointer):
        self.name = id
        self.pointer = pointer
        self.isopen = False
        self.isclosed = True
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True  # Daemon thread will exit when the main program exits
        self.thread.start()
        self.connectCallBackFuncEx = connectCallBackEx(self.deviceLinkNotify)
        self.frameCallbackFuncEx = callbackFuncEx(self.onGetFrameEx)
        self.camera_needs_Reset =False
        self.g_cameraStatusUserInfo = b"statusInfo"
    def onGetFrameEx(self,frame, userInfo):
        print(frame)
        start = time.time()
     
        nRet = frame.contents.valid(frame)
        if nRet != 0:
            print("Frame is invalid!")
            frame.contents.release(frame)
        else:

            frame_ = frame.contents.getBlockId(frame)
        
            print("Camera : Received New Trigger {}".format(frame_))

            imageParams = IMGCNV_SOpenParam()
            imageParams.dataSize = frame.contents.getImageSize(frame)
            imageParams.height = frame.contents.getImageHeight(frame)
            imageParams.width = frame.contents.getImageWidth(frame)
            imageParams.paddingX = frame.contents.getImagePaddingX(frame)
            imageParams.paddingY = frame.contents.getImagePaddingY(frame)
            imageParams.pixelForamt = frame.contents.getImagePixelFormat(frame)

            imageBuff = frame.contents.getImage(frame)
            userBuff = c_buffer(b'\0', imageParams.dataSize)
            memmove(userBuff, c_char_p(imageBuff), imageParams.dataSize)

            frame.contents.release(frame)

            if imageParams.pixelForamt == EPixelType.gvspPixelMono8:
                grayByteArray = bytearray(userBuff)
                cvImage = numpy.array(grayByteArray).reshape(imageParams.height, imageParams.width)
            else:
                rgbSize = c_int()
                rgbBuff = c_buffer(b'\0', imageParams.height * imageParams.width * 3)

                nRet = IMGCNV_ConvertToBGR24(cast(userBuff, c_void_p), \
                                            byref(imageParams), \
                                            cast(rgbBuff, c_void_p), \
                                            byref(rgbSize))

                colorByteArray = bytearray(rgbBuff)
                cvImage = numpy.array(colorByteArray).reshape(imageParams.height, imageParams.width, 3)

            # # Encode cvImage to base64
            # encoded_image = image_to_base64(cvImage)

            # # Prepare data to be sent over WebSocket
            # data = {
            #     "image": encoded_image,
            #     "height": imageParams.height,
            #     "width": imageParams.width,
            #     "format": "mono8" if imageParams.pixelForamt == EPixelType.gvspPixelMono8 else "rgb24",
            #     "cycle_start": start,
            #     "frame": frame_
            # }

            # # Convert data to JSON string
            # data_json = json.dumps(data)
            # end_time = time.time()

            # Calculate and print time taken
        
            # try:
            #     start_time = time.time()
            #     # Send JSON string over WebSocket
            #     print("Camera : Sending Image to Backend" )
            #     client.send_message(data_json)
            #     print("Camera : Waiting For Next Trigger" )
            #     end_time = time.time()

            #     # Calculate and print time taken
            

            # except Exception as ex:
            #     print(ex)



    def deviceLinkNotify(self,connectArg, linkInfo):
        print(linkInfo)
        if EVType.offLine == connectArg.contents.m_event:
            print("Camera : Camera has gone offline" )
            print("Camera :",self.g_cameraStatusUserInfo)
            self.camera_needs_Reset = True
        elif EVType.onLine == connectArg.contents.m_event:
            print("Camera : Camera has come online,")
            self.camera_needs_Reset = True
            
            
    def subscribeCameraStatus(self,camera):
    
        eventSubscribe = pointer(GENICAM_EventSubscribe())
        eventSubscribeInfo = GENICAM_EventSubscribeInfo()
        eventSubscribeInfo.pCamera = pointer(camera)
        nRet = GENICAM_createEventSubscribe(byref(eventSubscribeInfo), byref(eventSubscribe))
        if ( nRet != 0):
            print("create eventSubscribe fail!")
            return -1
        
        nRet = eventSubscribe.contents.subscribeConnectArgsEx(eventSubscribe, self.connectCallBackFuncEx, self.g_cameraStatusUserInfo)
        if ( nRet != 0 ):
            print("subscribeConnectArgsEx fail!")
    
            eventSubscribe.contents.release(eventSubscribe)
            return -1  
        
    
        eventSubscribe.contents.release(eventSubscribe) 
        return 0


    # 反注册相机连接状态回调
    def unsubscribeCameraStatus(self,camera):
        # 反注册上下线通知
        eventSubscribe = pointer(GENICAM_EventSubscribe())
        eventSubscribeInfo = GENICAM_EventSubscribeInfo()
        eventSubscribeInfo.pCamera = pointer(camera)
        nRet = GENICAM_createEventSubscribe(byref(eventSubscribeInfo), byref(eventSubscribe))
        if ( nRet != 0):
            print("create eventSubscribe fail!")
            return -1
            
        nRet = eventSubscribe.contents.unsubscribeConnectArgsEx(eventSubscribe, self.connectCallBackFuncEx, self.g_cameraStatusUserInfo)
        if ( nRet != 0 ):
            print("unsubscribeConnectArgsEx fail!")
            # 释放相关资源
            eventSubscribe.contents.release(eventSubscribe)
            return -1
        
        # 不再使用时，需释放相关资源
        eventSubscribe.contents.release(eventSubscribe)
        return 0   



    # 打开相机
    def openCamera(self,camera):
        # 连接相机

        nRet = camera.connect(camera, c_int(GENICAM_ECameraAccessPermission.accessPermissionControl))
       
        if ( nRet != 0 ):
            print("camera connect fail!")
            return -1
        else:
            print("camera connect success.")
    
        # 注册相机连接状态回调
        nRet = self.subscribeCameraStatus(camera)
        if ( nRet != 0 ):
            print("subscribeCameraStatus fail!")
            return -1

        return 0

    # 关闭相机
    def closeCamera(self,camera):
        # 反注册相机连接状态回调
        nRet = self.unsubscribeCameraStatus(camera)
        if ( nRet != 0 ):
            print("unsubscribeCameraStatus fail!")
            return -1
    
        # 断开相机
        nRet = camera.disConnect(byref(camera))
        if ( nRet != 0 ):
            print("disConnect camera fail!")
            return -1
        
        return 0    

    def run(self):
        try:
            """This method can be overridden with logic that needs to run in the background."""

            print("Camera : Opening Camera")
            nRet = self.openCamera(self.pointer)
         
            if ( nRet != 0 ):
                self.openCamera = False
                
            print("Camera : Closing Camera")
            # 创建流对象
            streamSourceInfo = GENICAM_StreamSourceInfo()
            streamSourceInfo.channelId = 0
            streamSourceInfo.pCamera = pointer(self.pointer)
            
            streamSource = pointer(GENICAM_StreamSource())
            nRet = GENICAM_createStreamSource(pointer(streamSourceInfo), byref(streamSource))
            if ( nRet != 0 ):
                print("create StreamSource fail!")
                return -1
            
            # 通用属性设置:设置触发模式为off --根据属性类型，直接构造属性节点。如触发模式是 enumNode，构造enumNode节点
            # 自由拉流：TriggerMode 需为 off
            trigModeEnumNode = pointer(GENICAM_EnumNode())
            trigModeEnumNodeInfo = GENICAM_EnumNodeInfo() 
            trigModeEnumNodeInfo.pCamera = pointer(self.pointer)
            trigModeEnumNodeInfo.attrName = b"TriggerMode"
            nRet = GENICAM_createEnumNode(byref(trigModeEnumNodeInfo), byref(trigModeEnumNode))
            if ( nRet != 0 ):
                print("create TriggerMode Node fail!")
                # 释放相关资源
                streamSource.contents.release(streamSource) 
                return -1
            print("Camera : Camera Set To Trigger Mode [On]")
            nRet = trigModeEnumNode.contents.setValueBySymbol(trigModeEnumNode, b"On")
            if ( nRet != 0 ):
                print("set TriggerMode value [On] fail!")
                # 释放相关资源
                trigModeEnumNode.contents.release(trigModeEnumNode)
                streamSource.contents.release(streamSource) 
                return -1
            
            # 需要释放Node资源    
            trigModeEnumNode.contents.release(trigModeEnumNode) 
                
        
            userInfo = b"test"
            nRet = streamSource.contents.attachGrabbingEx(streamSource, self.frameCallbackFuncEx, userInfo)    
            if ( nRet != 0 ):
                print("attachGrabbingEx fail!")
                # 释放相关资源
                streamSource.contents.release(streamSource)  
                return -1

            print("Camera : Attached GrabbingEx")
            # 开始拉流
            nRet = streamSource.contents.startGrabbing(streamSource, c_ulonglong(0), \
                                                    c_int(GENICAM_EGrabStrategy.grabStrartegySequential))
            if( nRet != 0):
                print("startGrabbing fail!")
                # 释放相关资源
                streamSource.contents.release(streamSource)   
                return -1
            print("Camera : Started GrabbingEx")  
        
            while 1:
                if self.camera_needs_Reset:
                    # 反注册回调函数
                    
                    print("Needs Reset:",streamSource)
                    nRet = streamSource.contents.detachGrabbingEx(streamSource, self.frameCallbackFuncEx, userInfo) 
                    if ( nRet != 0 ):
                        print("detachGrabbingEx fail!")
                        # 释放相关资源
                        streamSource.contents.release(streamSource)  
                        return -1

                    # 停止拉流
                    nRet = streamSource.contents.stopGrabbing(streamSource)
                    if ( nRet != 0 ):
                        print("stopGrabbing fail!")
                        # 释放相关资源
                        streamSource.contents.release(streamSource)  
                        return -1

                

                    # 关闭相机
                    nRet = self.closeCamera(self.pointer)
                    if ( nRet != 0 ):
                        print("closeCamera fail")
                        # 释放相关资源
                        streamSource.contents.release(streamSource)   
                        return -1
                    
                    # 释放相关资源
                    streamSource.contents.release(streamSource)   
                    
                
                    self.camera_needs_Reset = False
                    time.sleep(5)
                    self.run()
        except Exception as ex:
            print("Failed to reset camera")
            print(ex)
