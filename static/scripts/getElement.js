document.getElementById("runButton").addEventListener("click", async () => {
    const response = await fetch("/run-script", { method: "POST" });
    const data = await response.json();
    document.getElementById("output").textContent = data.output || "Error running script.";
});
