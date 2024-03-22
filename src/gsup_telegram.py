# support for Telegram Messenger use




def setupTelegram():
    """Send info to Telegram messenger"""

    fncname = "setupTelegram: "

    dprint(fncname)
    setIndent(1)

    title    = "Telegram Messenger Properties "
    msgbox   = QMessageBox()
    msgbox.setWindowTitle(title)
    msgbox.setIcon(QMessageBox.Warning)
    msgbox.setFont(gglobs.fontstd)

    try:
        import telegram
        # raise Exception("test setupTelegram")

    except Exception as e:
        msg  = "Python module 'telegram' was not found.\n\n\n"
        msg += "This module is required to communicate with the Telegram Messenger.\n\n\n"
        msg += "Verify that 'python-telegram-bot' is installed using GeigerLog tool: 'gtools/GLpipcheck.py'.\n\n\n"
        msg += "GeigerLog will continue, but Telegram cannot be used."
        exceptPrint(e, msg)
        # efprint(msg)
        playWav("err")
        msgbox.setText(msg)
        retval = msgbox.exec()
        setIndent(0)
        return

    try:
        gglobs.TelegramBot = telegram.Bot(token=gglobs.TelegramToken)
        # dprint(fncname + str(gglobs.TelegramBot.get_me()))
        # raise Exception("test setupTelegram 2")
        fprint("got telegram.bot")

        myupdate = telegram.Update(207713860)
        print("myupdate.effectie_chat:", myupdate.effective_chat)

    except Exception as e:
        msg = "Telegram Messenger is not accessible.\n\n\n"
        msg += "Verify that you have set the proper Telegram token!\n\n\n"
        exceptPrint(fncname + str(e), msg)
        playWav("err")
        msgbox.setText(msg)
        retval = msgbox.exec()
        setIndent(0)
        return

    try:
        updates = gglobs.TelegramBot.get_updates()
        print("updates", len(updates))
        # print("updates[0]", len(updates[0]))
        print(type(updates))

        for i, a in enumerate(updates):
            fprint(i, updates[i])
            dprint(i, updates[i])

        print("updates[1].message.chat.id: ", updates[1].message.chat.id)

        print()

        # gglobs.TelegramChatID = updates[0].message.from_user.id
        gglobs.TelegramChatID = updates[1].message.chat.id

        dprint("gglobs.TelegramChatID: ", gglobs.TelegramChatID)
        #raise Exception("test setupTelegram 3")

    except Exception as e:
        msg  = "Telegram Messenger is not accessible.\n\n\n"
        msg += "You may need to first send a message to your bot from your Telegram App/Desktop.\n\n\n"
        exceptPrint(fncname + str(e), msg)
        playWav("err")
        msgbox.setText(msg)
        retval = msgbox.exec()
        setIndent(0)
        return

    retval = setTelegramProperties()
    if retval == 0:
        dprint(fncname + "Cancelled, Properties unchanged")

    else:
        dprint(fncname + "ok, new settings: Activation: {} UpdateCycle : {} min".format(
                                        gglobs.TelegramActivation,
                                        gglobs.TelegramUpdateCycle)
                                        )

        fprint(header(title))
        fprint("Activation:",   "{}".format("Yes" if gglobs.TelegramActivation else "No"))
        fprint("Update Cycle:", "{} min".format(gglobs.TelegramUpdateCycle))

        gglobs.TelegramLastUpdate = 0 # reset so it will be updated on next log

    setIndent(0)


def setTelegramProperties():
    """Set activation and cycle time"""

    fncname = "setTelegramProperties: "

    lmean = QLabel("Activate Updates")
    lmean.setAlignment(Qt.AlignLeft)
    lmean.setMinimumWidth(200)

    r01=QRadioButton("Yes")
    r02=QRadioButton("No")
    r01.setChecked(False)
    r02.setChecked(False)
    r01.setToolTip("Activate 'Yes' to send Updates to Telegram in regular intervals")
    r02.setToolTip("Activate 'No' to never send Updates to Telegram")
    powergroup = QButtonGroup()
    powergroup.addButton(r01)
    powergroup.addButton(r02)
    hbox0=QHBoxLayout()
    hbox0.addWidget(r01)
    hbox0.addWidget(r02)
    hbox0.addStretch()
    if gglobs.TelegramActivation:   r01.setChecked(True)
    else:                           r02.setChecked(True)

    lctime = QLabel("Update Cycle Time [minutes]\n(at least 1 min)")
    lctime.setAlignment(Qt.AlignLeft)
    ctime  = QLineEdit()
    ctime.setToolTip('Enter X to update Telegram every X minutes')
    ctime.setText("{:0.5g}".format(gglobs.TelegramUpdateCycle))

    graphOptions=QGridLayout()
    graphOptions.addWidget(lmean,          0, 0)
    graphOptions.addLayout(hbox0,          0, 1)
    graphOptions.addWidget(lctime,         1, 0)
    graphOptions.addWidget(ctime,          1, 1)
    graphOptions.addWidget(QLabel(""),     2, 0)

    d = QDialog() # set parent to None to popup in center of screen
    d.setWindowIcon(gglobs.iconGeigerLog)
    d.setFont(gglobs.fontstd)
    d.setWindowTitle("Telegram Messenger Properties")
    d.setWindowModality(Qt.NonModal)
    d.setMinimumWidth(300)

    bbox = QDialogButtonBox()
    bbox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok )
    bbox.accepted.connect(lambda: d.done(100))
    bbox.rejected.connect(lambda: d.done(0))

    layoutV = QVBoxLayout(d)
    layoutV.addLayout(graphOptions)
    layoutV.addWidget(bbox)

    retval = d.exec()
    #print("reval:", retval)

    if retval > 0:
        # Activation
        if r01.isChecked():
            gglobs.TelegramActivation = True
            gglobs.exgg.TelegramAction.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_Telegram.png'))))
        else:
            gglobs.TelegramActivation = False
            gglobs.exgg.TelegramAction.setIcon(QIcon(QPixmap(os.path.join(gglobs.gresPath, 'icon_Telegram_inactive.png'))))

        # Update Cycle Time
        uctime = ctime.text().replace(",", ".")  #replace any comma with dot
        try:    dt  = max(round(abs(float(uctime)), 2), 1)
        except: dt  = gglobs.TelegramUpdateCycle
        gglobs.TelegramUpdateCycle = dt

    return retval


def getTelegramMessage():
    """assemble the data"""

    varvalues = {}
    strdata   = "   {:13s}: {} min\n".format("Update Cycle", gglobs.TelegramUpdateCycle)

    DeltaT    = gglobs.TelegramUpdateCycle  # DeltaT in minues, TelegramUpdateCycle in min
    try:
        for vname in gglobs.varsCopy:
            if gglobs.varLoggable[vname]:
                myformat = "   {:13s}: {:0.3f}\n"

                # next line sieht falsch aus????
                # old: varvalues[vname] = np.nanmean(getDataInLimits(vname, DeltaT))
                # new:
                timedata, vardata, plotTimeDelta = getTimeCourseInLimits(vname, DeltaT)
                varvalues[vname] = np.nanmean(vardata)

                strdata += myformat.format(vname, varvalues[vname])

        # print(strdata)
        # raise Exception("reading all vars")

    except Exception as e:
        msg  = "No proper data available.\n\n\n"
        msg += "Are there any data shown in the plot?\n\n\n"
        exceptPrint(fncname + str(e), msg)
        playWav("err")
        msgbox.setText(msg)
        retval = msgbox.exec()
        return ""

    return strdata


def updateTelegram():
    """get a new data set and send as message to Telegram"""

    if gglobs.TelegramChatID is not None:

        # get the data as string
        msg = getTelegramMessage()

        # send update to Telegram
        gglobs.TelegramBot.send_message(text= "<pre>" + msg + "</pre>", chat_id=gglobs.TelegramChatID, parse_mode = "HTML")

        # save to db and print to logPad
        gglobs.exgg.addMsgToLog("SUCCESS", "Updating Telegram with: " + msg.replace(" ", "").replace("\n", " "))


###########################################################