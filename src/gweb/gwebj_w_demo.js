// js for Web Page Widget-Demo




async function WidgetMain(){

    document.title = "GeigerLog Widget-Demo";

    await getLastData();
    await getGeigerLogStatus();
    setButtonStates();

    setInterval(async function() {
        await getLastData();
        await getGeigerLogStatus();
        setButtonStates();
    }, MonRefresh);
}

WidgetMain();

