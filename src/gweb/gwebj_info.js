
// js for Web Page Info

async function InfoMain(){

    document.title = "Info";

    await getLastData();
    await getGeigerLogStatus();
    setButtonStates();

    setInterval(async function() {
        await getLastData();
        await getGeigerLogStatus();
        setButtonStates();
    }, MonRefresh);
}

InfoMain();

