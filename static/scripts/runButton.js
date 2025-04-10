document.getElementById('runButton').addEventListener('click', function() {
    fetch('/run-script', { method: 'POST' })
    .then(response => {
        if (response.ok) {

            document.getElementById('graphFrame').src = '/get-graph?' + new Date().getTime();
        } else {
            alert('Script çalıştırılamadı.');
        }
    })
    .catch(error => {
        console.error('Hata:', error);
        alert('Bir hata oluştu.');
    });
});
