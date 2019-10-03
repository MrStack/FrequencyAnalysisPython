# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 18:01:39 2019

@author: albert
"""

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
import numpy as np
import wave
import pyaudio


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.fontType = QtGui.QFont(QtGui.QFont('consolas', 10))
        self.buttonSize = QtCore.QSize(65, 40)

        self.audioFileNames = []
        self.audioFilePlayingIndex = 0
        self.audioFileCurrentChooseIndex = 0
        self.samplingFrequency = 0
        self.audioVec = 0
        self.audioList = QtWidgets.QListWidget(self)
        self.audioPlayingFlag = False
        self.audioTimeChunkIndex = 0

        self.audioPlayTimer = QtCore.QTimer()
        self.audioPlayTimer.timeout.connect(self.audio_player)

        self.timeDomainLabel = QtWidgets.QLabel(self)
        self.frequencyDomainLabel = QtWidgets.QLabel(self)

        self.browseButton = QtWidgets.QPushButton('Browse\nfile', self)
        self.playButton = QtWidgets.QPushButton('Play', self)
        self.stopButton = QtWidgets.QPushButton('Stop', self)

        self.audioTimeDomain = QtWidgets.QGraphicsView(self)
        self.audioFrequencyDomain = QtWidgets.QGraphicsView(self)

        self.init_main_window()
        self.init_buttons()
        self.init_lists()
        self.init_canvas()
        self.init_labels()
        self.init_drawer()

    def open_audio_file(self):
        self.audioFileNames = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open file', 'D:/CloudMusic', "所有文件 (*);;音频文件 (*.wav)")
        # 如果没有打开任何文件，则不做任何操作，保留编辑框中之前的文本信息
        if len(self.audioFileNames[0]) == 0:
            return
        else:
            self.audioList.addItems(self.audioFileNames[0])
            self.repaint()

    def init_buttons(self):
        self.browseButton.setFont(self.fontType)
        self.browseButton.clicked.connect(self.open_audio_file)
        self.browseButton.resize(self.buttonSize)
        self.browseButton.move(1020, 20)

        self.playButton.setFont(self.fontType)
        self.playButton.clicked.connect(self.play_audio)
        self.playButton.resize(self.buttonSize)
        self.playButton.move(1125, 20)

        self.stopButton.setFont(self.fontType)
        self.stopButton.clicked.connect(self.stop_audio)
        self.stopButton.resize(self.buttonSize)
        self.stopButton.move(1230, 20)

    def init_lists(self):
        self.audioList.setFont(self.fontType)
        self.audioList.setFixedSize(300, 670)
        self.audioList.move(1010, 80)

    def init_main_window(self):
        self.setWindowTitle('Frequency analysis system')
        self.setFixedSize(1333, 768)

    def init_canvas(self):
        timeDomainRect = QtCore.QRect(10, 10, 930, 350)
        frequencyDomainRect = QtCore.QRect(10, 390, 930, 350)

        self.audioTimeDomain.setGeometry(timeDomainRect)
        self.audioFrequencyDomain.setGeometry(frequencyDomainRect)

    def init_labels(self):
        self.timeDomainLabel.setText('Time domain')
        self.timeDomainLabel.setFont(self.fontType)
        self.timeDomainLabel.move(450, 365)

        self.frequencyDomainLabel.setText('Frequency domain')
        self.frequencyDomainLabel.setFont(self.fontType)
        self.frequencyDomainLabel.move(432, 745)

    def init_drawer(self):
        geo = self.audioTimeDomain.geometry()
        self.audioTimeDomain = Drawer(self.audioTimeDomain)
        self.audioTimeDomain.set_canvas_geometry(0, 0, geo.width(), geo.height())
        self.audioTimeDomain.set_ylimits(-32000, 32000)

        geo = self.audioFrequencyDomain.geometry()
        self.audioFrequencyDomain = Drawer(self.audioFrequencyDomain)
        self.audioFrequencyDomain.set_canvas_geometry(0, 0, geo.width(), geo.height())
        self.audioFrequencyDomain.set_ylimits(0, 10000)

    def audio_player(self):
        if not self.audioPlayingFlag:
            return
        self.wf.setpos(self.audioTimeChunkIndex)
        self.data = self.wf.readframes(self.CHUNK)
        self.audioTimeChunkIndex += self.CHUNK
        if self.data != b'':
            self.datause = np.fromstring(self.data, np.short)
            self.datause.shape = -1, 2
            self.datause = self.datause.T
            self.oneChannel = self.datause[0].tolist()
            startTime = self.audioTimeChunkIndex * 1 / self.params[2]
            endTime = startTime + self.CHUNK * 1 / self.params[2]
            self.time = np.arange(startTime, endTime, 1/self.params[2])[:self.CHUNK]

            if len(self.oneChannel) < self.CHUNK:
                zeros = np.zeros(self.CHUNK-len(self.oneChannel)).tolist()
                self.oneChannel.extend(zeros)
            self.audioTimeDomain.plot(x=self.time, y=self.oneChannel)

            FY = np.fft.fft(self.oneChannel, self.CHUNK)
            AY = np.abs(FY)
            AY = AY/(self.CHUNK/2)
            AY[0] = AY[0]/2
            F = np.arange(0, self.CHUNK)*self.params[2]/self.CHUNK
            x = F[:self.CHUNK//2]
            y = AY[:self.CHUNK//2]
            #width = self.params[2]/self.CHUNK
            #self.audioFrequencyDomain.bar_plot(x=x, y=y, width=width)
            self.audioFrequencyDomain.plot(x=x, y=y)

            if self.audioTimeChunkIndex >= self.params[3] - self.CHUNK - 1:
                if self.audioFileCurrentChooseIndex < len(self.audioFileNames[0]):
                    self.audioFileCurrentChooseIndex += 1
                    self.audioTimeChunkIndex = 0
                    self.read_audio_file()
                else:
                    self.audioFileCurrentChooseIndex = 0
                    self.audioTimeChunkIndex = 0
                    self.read_audio_file()

                return
            self.stream.write(self.data)
        else:
            pass

#            self.audioTimeDomain.plot(x=[0], y=[0])
#            self.audioFrequencyDomain.plot(x=[0], y=[0])
#            self.stop_audio()

    def read_audio_file(self):
        self.file = self.audioFileNames[0][self.audioFileCurrentChooseIndex]
        self.CHUNK = 2048
        self.wf = wave.open(self.file, 'rb')
        self.p = pyaudio.PyAudio()

        self.params = self.wf.getparams()

    def play_audio(self):
        self.read_audio_file()
        #self.audioTimeChunkIndex = 10160000
        self.stream = self.p.open(format=self.p.get_format_from_width(self.wf.getsampwidth()),
                        channels=self.wf.getnchannels(),
                        rate=self.wf.getframerate(),
                        output=True)

        if self.audioPlayingFlag:
            self.playButton.setText('Play')
            self.audioPlayingFlag = False
            self.audioPlayTimer.stop()
            self.stream.stop_stream()

        else:
            self.playButton.setText('Pause')
            self.audioPlayingFlag = True
            self.stream.start_stream()
            self.audioPlayTimer.start(int(1/self.params[2]*self.CHUNK*1000)-15)

    def stop_audio(self):
        self.playButton.setText('Play')
        self.audioPlayingFlag = False
        self.audioTimeChunkIndex = 0
        self.audioPlayTimer.stop()
        self.stream.close()
        self.p.terminate()


class Drawer(pg.PlotWidget):
    def __init__(self, parent_window):
        super().__init__(parent=parent_window)
        self.curve = self.plotItem.plot([0])
        pass

    def set_canvas_geometry(self, x, y, width, height):
        self.setGeometry(x, y, width, height)

    def paint_clear(self):
        self.curve.clearPlots()

    def set_xlimits(self, start, end):
        self.setXRange(start, end)

    def set_ylimits(self, start, end):
        self.setYRange(start, end)

    def plot(self, x, y, pen=(255, 255, 255)):
        #self.curve.clearPlots()
        #self.curve.plot(x=x, y=y)
        self.curve.setData(x=x, y=y, pen=pen)
        pass

#    def plot(self, x, y, pen=(255, 255, 255)):
#        self.curve.clearPlots()
#        self.curve.plot(x=x, y=y)

    def bar_plot(self, x, y, width, pen=(255, 255, 255)):
        self.plotItem.clear()
        bar = pg.BarGraphItem(x=x, height=y, width=width, pen=pen)
        self.addItem(bar)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Main = MainWindow()
    Main.show()

    sys.exit(app.exec_())
