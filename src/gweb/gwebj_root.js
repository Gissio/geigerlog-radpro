
// js for Web Page Root

async function RootMain(){

    document.title = "GeigerLog Monitor Server";

    await getLastData();
    await getGeigerLogStatus();
    setButtonStates();

    oldLogStatus = LogStatus;
    console.log("MonMain: LogStatus: ", LogStatus, "oldLogStatus: ", oldLogStatus)

    setInterval(async function() {
        await getLastData();
        await getGeigerLogStatus();
        setButtonStates();
    }, MonRefresh);
}

RootMain();

