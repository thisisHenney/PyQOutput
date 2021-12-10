#!/usr/bin/env python
#-*-coding:utf8-*-
#!/bin/bash

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Notice
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# <1> Header
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Common
import os, sys
path_NextLib_PyQOutput_output_py = os.path.dirname(os.path.abspath(__file__))

# System Library


# NextLib Library
# from NextLib.cmn import *
from NextLib.qt4 import *


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# <2> Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Output Class
class OUTPUT_CLASS:
    def __init__(self, win=None):
        # Common
        self.win        = win

        # Process
        self.curPath    = homePath
        self.cmd        = ""
        self.env        = ""

        # Process Status
        self.bRunning   = False
        self.bError     = False
        self.bKill      = False

        # Process List
        self.arrProc        = []

        # Finish func
        self.arrFinishFunc  = []
        self.funcFinish     = False

        self.arrFinishArgv  = []
        self.argvFinish     = None

        # After finishing
        self.bFinishMsg     = False

        self.bErrorMsg      = False
        self.bErrorFunc     = False
        self.vError_Func    = False  # Virtual Function

        # Result
        self.iExitStatus    = 0
        self.output_Std     = "No Output Data"
        self.output_Err     = "No Error Data"

        # Setting
        self.bErrContinue   = False  # 에러발생해도 다음 명령어 실행 여부
        self.bDisplayCmd    = True

        return

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Main
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def New(self):
        self.win = QMainWindow()

        # Create Box
        self.wgEdit = QTextEdit()
        self.wgEdit.clear()
        self.win.setCentralWidget(self.wgEdit)

        # Create Boxes
        # self.wgInput = QLineEdit()
        # self.wgMain = QWidget()
        # self.mainBox = QVBoxLayout()
        # self.mainBox.setContentsMargins(0, 0, 0, 0)
        # self.mainBox.addWidget(self.wgEdit)
        # self.mainBox.addWidget(self.wgInput)
        # self.wgMain.setLayout(self.mainBox)
        # self.win.setCentralWidget(self.wgMain)

        # Process
        self.process = QProcess()

        # Connect
        self.process.started.connect(self.Connect_Started)

        self.process.readyReadStandardOutput.connect(self.Connect_Output_OK)
        self.process.readyReadStandardError.connect(self.Connect_Output_Error)

        self.process.finished.connect(self.Connect_Finished)
        self.process.error.connect(self.Connect_Error)

        # Set
        self.wgEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.wgEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.wgEdit.setStyleSheet("font: 9 pt \'Ubuntu Mono\';")
        self.wgEdit.setReadOnly(True)

        self.Set_Scroll_Tracking()
        self.Set_Scroll_Bottom()

        self.Set_Text()
        return

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # [1] New
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Connect
    def Connect_Started(self):  # 시작할 때
        self.bRunning = True
        return

    def Connect_Error(self):    #
        self.Set_Scroll_Bottom()
        self.Add_Text_Error("\n>> Stopped")
        #
        self.bError = True
        return

    def Connect_Output_OK(self):    # 실행 중
        self.output_Std = self.process.readAllStandardOutput().data()
        self.Add_Text(self.output_Std[:-1])
        return

    def Connect_Output_Error(self):  # 실행 중 에러가 뜰 경우
        self.Set_Scroll_Bottom()
        self.output_Err = self.process.readAllStandardError().data()
        self.Add_Text_Error_Data(self.output_Err[:-1])
        #
        self.bError = True
        return

    def Connect_Finished(self, statusExit):      # 현재 명령이 종료되었을 경우(Error, Kill 포함)
        self.iExitStatus = statusExit  # 0 is exited normally
        self.bRunning = False

        # Finishing Function
        if self.funcFinish is not False:
            if self.argvFinish is not None:
                self.funcFinish(self.argvFinish)
            else:
                self.funcFinish()
            self.funcFinish = False
            self.argvFinish = None

        # Kill
        if self.bKill:
            self.Set_Scroll_Bottom()
            # self.Add_Text_End("\n>> Process terminated")  # 다른데서 알려줌

            # A finish function when killing
            if self.bErrorMsg:
                ErrorMsg(self.win, "Process stopped")
            return

        # Error
        if self.bError:
            self.Set_Scroll_Bottom()
            self.Add_Text_Error(T_(">> Stopped"))  # "\n>> The process stopped with an error"
            if not self.bErrContinue:   # 에러 발생 시 다음 커맨드 실행 안함
                if self.bErrorMsg:
                    ErrorMsg(self.win, "Error")
                # Cancel remaining jobs
                self.Reset_Command()
                return

        # Normal
        if not self.bError:
            self.Add_Text_End(T_(">> Done"))

        # Next Process
        if len(self.arrProc) > 0:
            # Start next process
            self.Run(self.arrProc.pop(0), self.env, func=self.arrFinishFunc.pop(0), argv=self.arrFinishArgv.pop(0))
        else:   # 정상적으로 실행되었을 때 모든 명령어(arrProc)가 실행된 후 vFinish_Func가 실행됨
            if self.bFinishMsg:
                Msg(self.win, "Done")
        return

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # [2] Run
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def Set_Defaults(self, path=""):     # 설정을 그대로 두고 화면만 초기화
        #
        # Init
        self.curPath = path

        # Show
        self.Set_Text()
        if path:
            self.Set_Current_Dir(self.curPath)
        self.Set_Scroll_Bottom()
        return

    def Reset_Command(self):
        # Process List
        self.arrProc = []

        # Finish func
        self.arrFinishFunc = []
        self.funcFinish = False

        self.arrFinishArgv = []
        self.argvFinish = None
        return

    def Run(self, cmd, env="", runType="/bin/bash", func=False, argv=None, bShow=True):
        # Init
        self.Set_Scroll_Bottom()

        # Check
        if self.bRunning :
            WarningMsg(self.win, "Another process is already running")
            return

        # Finish func
        self.funcFinish = func
        self.argvFinish = argv

        # Merge
        if isinstance(cmd, list):
            cmd = Merge_List(cmd, " && ")

        # Start
        self.cmd = cmd
        strCmd = T_("\n")
        if self.bDisplayCmd and bShow:
            command = self.cmd.split(" && ")
            for dd in command:
                if dd:
                    strCmd += T_(">> %s", dd)
            # strCmd += T_("\n")
        #
        self.Add_Text_Cmd(strCmd)
        if not env == "":
            self.env = env
            cmd = self.env + " && " + self.cmd

        # Start
        self.process.start(QString(runType), QStringList() << "-c" << cmd )
        if self.process.waitForStarted():
            # 제대로 시작이 되었을 경우
            self.bError = False
            self.bRunning = True
            self.bKill = False
        # self.process.waitForFinished(-1) # 종료될 때까지 기다리는 함수

        return

    def RunAfter(self, cmd, env="", runType="/bin/bash", func=False, argv=None):
        if self.bRunning:
            self.arrProc.append(cmd)
            self.arrFinishFunc.append(func)
            self.arrFinishArgv.append(argv)
        else:
            self.Run(cmd, env, runType, func=func, argv=argv)
        return

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # [3] End
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def End(self, bShow_Msg=False):
        # Check
        self.Kill_Process(bShow_Msg)

        return

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # [@] Function
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # --------------------------------------------------------------------------
    # Edit
    # --------------------------------------------------------------------------
    # Show
    def Set_Text(self, text="Ready", color="black", bold=50):
        self.Set_Font(color, bold)
        self.wgEdit.setText(QString(text))
        return

    def Add_Text(self, text="Text added", color="black", bold=50):
        self.Set_Font(color, bold)
        self.wgEdit.append(QString(text))
        self.Set_Font_Normal()
        return

    def Add_Text_Cmd(self, text="Command added"):
        self.Set_Font_Start()
        self.wgEdit.append(QString(text))
        self.Set_Font_Normal()
        return

    def Add_Text_End(self, text="done"):
        self.Set_Font_Finish()
        self.wgEdit.append(QString(text))
        self.Set_Font_Normal()
        return

    def Add_Text_Error(self, text="Error"):
        self.Set_Font_Error()
        self.wgEdit.append(QString(text))
        self.Set_Font_Normal()
        return

    def Add_Text_Error_Data(self, text="Error Data"):
        self.Set_Font_Error_Data()
        self.wgEdit.append(QString(text))
        self.Set_Font_Normal()
        return

    # Font
    def Set_Font(self, color="black", bold=50):
        self.wgEdit.setTextColor(QColor(color))
        self.wgEdit.setFontWeight(bold)
        return

    def Set_Font_Normal(self, bold=50):
        self.Set_Font("black", bold)
        return

    def Set_Font_Start(self, bold=75):
        self.Set_Font("green", bold)
        return

    def Set_Font_Finish(self, bold=75):
        self.Set_Font("blue", bold)
        return

    def Set_Font_Error(self, bold=75):
        self.Set_Font("red", bold)
        return

    def Set_Font_Error_Data(self, bold=50):
        self.Set_Font("gray", bold)
        return

    # Scroll
    def Set_Scroll_Tracking(self, bMode=True):
        self.wgEdit.verticalScrollBar().setTracking(bMode)
        return

    def Set_Scroll_Bottom(self):
        self.wgEdit.verticalScrollBar().setValue(self.wgEdit.verticalScrollBar().maximum())
        return

    # --------------------------------------------------------------------------
    # Set
    # --------------------------------------------------------------------------
    def Set_Current_Dir(self, path):
        self.curPath = path
        self.process.setWorkingDirectory(self.curPath)

        # Show
        self.wgEdit.setFontUnderline(True)
        self.Add_Text("\n>> Current Directory: %s" %self.curPath, "black", 75)
        self.wgEdit.setFontUnderline(False)
        return

    # def Set_Environment(self, data):  # 언제 쓰는 건지 모름
    #     # cur_env = QProcessEnvironment.systemEnvironment()
    #     # cur_env = QProcessEnvironment.systemEnvironment().value('key', 'value')
    #
    #     # cur_env.insert('PATH', cur_env.value('PATH') + QString(data))
    #     # self.process.setProcessEnvironment(cur_env)
    #     # self.process.setEnvironment(QStringList()<<data)
    #     return

    # --------------------------------------------------------------------------
    # Process
    # --------------------------------------------------------------------------
    def Kill_Process(self, bShow_Msg=False):
        # Init
        curPID = self.process.pid()

        # Check
        if curPID > 0:
            # Notice
            # self.process.kill()   # This function cannot kill all child processes.

            # Get
            output = pexpect.spawn("pgrep -P %d" % curPID)
            output.expect(pexpect.EOF)
            output = output.before.decode()
            splitOutput = output.split("\r\n")

            # Kill Child
            for dd in splitOutput:
                if dd:
                    strCMD = "kill -KILL %s" % dd
                    Execute(strCMD)

            # Kill Parent
            strCMD = "kill -KILL %d" % curPID
            Execute(strCMD)

            # Set
            self.Set_Scroll_Bottom()
            self.bKill = True
        else:
            if bShow_Msg:
                NoticeMsg(self.win, "There are no jobs running!")
        return

    def Pause_Process(self):
        # Init
        curPID = self.process.pid()

        # Check
        if curPID == 0:
            NoticeMsg(self.win, "There are no jobs running!")
        else:
            Execute("kill -STOP %d" % curPID)
        return

    def Continue_Process(self):
        # Init
        curPID = self.process.pid()

        # Check
        if curPID == 0:
            NoticeMsg(self.win, "There are no jobs running!")
        else:
            Execute("kill -CONT %d" % curPID)
        return

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# <4> Functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# <5> Run
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
