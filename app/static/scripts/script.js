/*=============== SHOW MENU ===============*/
const showMenu = (toggleId, navId) => {
  const toggle = document.getElementById(toggleId),
      nav = document.getElementById(navId)

  toggle.addEventListener('click', () => {
      nav.classList.toggle('show-menu')
      toggle.classList.toggle('show-icon')
  })
}

showMenu('nav-toggle', 'nav-menu')

/*=============== FILE MENU ===============*/
let selectedFile = null;

document.getElementById("hiddenFileInput").addEventListener("change", function () {
  selectedFile = this.files[0];
  const validExtensions = ['csv', 'xlsx', 'xml', 'json'];
  const fileExtension = selectedFile.name.split('.').pop().toLowerCase();

  if (!validExtensions.includes(fileExtension)) {
    alert("Geçersiz dosya formatı. Lütfen csv, xlsx, xml veya json dosyası seçin.");
    this.value = '';
  }
});

document.getElementById("glowButton").addEventListener("click", () => {
  document.getElementById("hiddenFileInput").click();
});

document.getElementById('hiddenFileInput').addEventListener('change', function(event) {
  const file = event.target.files[0];
  if (!file) return;

  const chunkSize = 5 * 1024; // 5 KB
  const blob = file.slice(0, chunkSize);

  const reader = new FileReader();
  reader.onload = function(e) {
    const text = e.target.result;
    const lines = text.split(/\r?\n/).slice(0, 10).join("\n");
    const payload = JSON.stringify({ sample: lines });

    fetch('/upload/get-head-api', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload
    })
    .then(response => response.json())
    .then(data => {
      if (data.head) {
        const helperPanel = document.getElementById('helper-panel');
        const helperContent = document.getElementById('helper-head-content');
        const rows = JSON.parse(data.head);
        if (rows && rows.length > 0) {
          const columns = Object.keys(rows[0]);
          let table = '<table style="width:100%;color:white;border-collapse:collapse;">';
          table += '<tr>' + columns.map(col => `<th>${col}</th>`).join('') + '</tr>';
          rows.forEach(row => {
            table += '<tr>' + columns.map(col => `<td>${row[col]}</td>`).join('') + '</tr>';
          });
          table += '</table>';
          helperContent.innerHTML = `<h4>Dosya Yüklendi - İlk Satırlar</h4><div class="scroll-container">${table}</div>`;
        } else {
          helperContent.innerHTML = "Veri bulunamadı.";
        }
        helperPanel.classList.add('expanded');
        document.querySelectorAll('.tablink').forEach(tab => {
          tab.classList.remove('active');
          if (tab.getAttribute('data-tab') === 'data-tab') tab.classList.add('active');
        });
        document.querySelectorAll('.tabcontent').forEach(content => content.classList.remove('active'));
        document.getElementById('data-tab').classList.add('active');
      }
    })
    .catch(err => console.error("get-head-api hatası:", err));

    fetch('/upload/get-columns-api', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload
    })
    .then(response => response.json())
    .then(data => {
      if (data.columns) {
        fillDropdowns(data.columns);
      }
    })
    .catch(err => console.error("get-columns-api hatası:", err));
  };
  reader.readAsText(blob);
});

function showDataPreview(rows) {
    const previewDiv = document.getElementById('data-preview');
    previewDiv.innerHTML = '';
}

function fillDropdowns(columns) {
    const xAxis = document.getElementById('xAxis');
    const yAxis = document.getElementById('yAxis');
    xAxis.innerHTML = '';
    yAxis.innerHTML = '';
    columns.forEach(col => {
        xAxis.innerHTML += `<option value="${col}">${col}</option>`;
        yAxis.innerHTML += `<option value="${col}">${col}</option>`;
    });
    const datalist = document.getElementById('columns-list');
    if (datalist) {
        datalist.innerHTML = '';
        columns.forEach(col => {
            const option = document.createElement('option');
            option.value = col;
            datalist.appendChild(option);
        });
    }
}

const dropdown1 = document.getElementById('dropdown1');
const dropdown2 = document.getElementById('dropdown2');
const dropdown3 = document.getElementById('dropdown3');
const projectTitle = document.getElementById("projectTitle").value;

function clearDropdown(dropdown) {
  dropdown.innerHTML = '<option value="">Seçim Yapın</option>';
  dropdown.disabled = false;
}

function populateDropdown(dropdown, options) {
  dropdown.innerHTML = '<option value="">Seçim Yapın</option>';
  options.forEach(option => {
    const opt = document.createElement('option');
    opt.value = option;
    opt.textContent = option;
    dropdown.appendChild(opt);
  });
  dropdown.disabled = false;
}

const navMenu = document.getElementById('nav-menu');
const navToggle = document.getElementById('nav-toggle');
const navClose = document.querySelector('.nav__close');

// DÜZELTME: Yüklenen dosyanın adını saklamak için global bir değişken.
let uploadedFileName = null;

/*=============== GÖNDER & POLLING ===============*/
document.getElementById("visualizeBtn").addEventListener("click", () => {
  const plotType = document.getElementById("plotType").value;
  const xAxis = document.getElementById("xAxis").value;
  const yAxis = document.getElementById("yAxis").value;
  const projectTitle = document.getElementById("projectTitle").value;

  if (!selectedFile) { alert("Lütfen bir dosya seçin."); return; }
  if (!projectTitle) { alert("Proje başlığı boş olamaz."); return; }
  if (!plotType) { alert("Lütfen bir grafik türü seçin."); return; }
  if (!xAxis) { alert("Lütfen bir X ekseni seçin."); return; }
  // Not: Histogram gibi bazı grafikler için Y ekseni zorunlu olmayabilir.
  // if (!yAxis) { alert("Lütfen bir Y ekseni seçin."); return; }

  const formData = new FormData();
  formData.append("file", selectedFile);
  
  // 1. Adım: Dosyayı yükle
  fetch(`/upload/${encodeURIComponent(projectTitle)}`, { method: "POST", body: formData })
    .then(response => {
      if (!response.ok) {
        throw new Error('Dosya yüklenemedi. Sunucu hatası: ' + response.status);
      }
      return response.json();
    })
    .then(uploadData => {
      if (!uploadData || !uploadData.file_name) {
        throw new Error("Dosya yüklendi ancak sunucudan dosya adı alınamadı.");
      }
      
      uploadedFileName = uploadData.file_name;
      showLogPanel();

      const stateMachineParams = new URLSearchParams();
      stateMachineParams.append('mode', 'visualize_only');
      stateMachineParams.append('output_type', 'raw');
      stateMachineParams.append('file_name', uploadedFileName);
      stateMachineParams.append('project_name', projectTitle);
      
      // EN ÖNEMLİ DÜZELTME: Grafik parametrelerini bu isteğe ekliyoruz.
      stateMachineParams.append('secim1', plotType); // plot_type
      stateMachineParams.append('secim2', xAxis);    // x_col
      stateMachineParams.append('secim3', yAxis);    // y_col

      return fetch('/state/run-state-machine', {
        method: 'POST',
        body: stateMachineParams
      });
    })
    .then(response => {
      if (response.ok) {
        // DÜZELTME: pollForGraphs fonksiyonuna 'projectTitle' gönderiliyor.
        pollForGraphs('raw', 'beforeFrame', null, projectTitle); 
      } else {
        return response.json().then(err => { throw new Error(err.message || "State machine başlatılamadı."); });
      }
    })
    .catch(err => {
      console.error("Hata:", err);
      alert(err.message || "Beklenmedik bir hata oluştu.");
    });
});

document.getElementById("addProcessBtn").addEventListener("click", () => {
    const selectedProcesses = getSelectedProcesses();
    if (!selectedProcesses) return;
    
    // DÜZELTME: İşlem yapmadan önce bir dosyanın yüklenmiş olduğundan emin ol.
    if (!uploadedFileName) {
        alert("Lütfen önce bir dosya yükleyip 'Görselleştir' butonuna basın.");
        return;
    }
    
    const projectTitle = document.getElementById("projectTitle").value;
    if (!projectTitle) { alert("Proje başlığı boş olamaz."); return; }

    const params = new URLSearchParams({
        mode: 'full_manual',
        output_type: 'refined',
        processes: JSON.stringify(selectedProcesses),
        project_name: projectTitle, 
        file_name: uploadedFileName 
    });

    fetch('/state/run-state-machine', {
        method: 'POST',
        body: params
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.message || "İşlemler gönderilirken hata oluştu."); });
        }
        return response.json();
    })
    .then(data => {
        showLogPanel();
        alert("İşlemler gönderildi ve analiz başladı!");
        // DÜZELTME: pollForGraphs fonksiyonuna 'projectTitle' gönderiliyor.
        pollForGraphs('raw', 'beforeProcessFrame', 'beforeDesc', projectTitle);
        pollForGraphs('refined', 'afterProcessFrame', 'afterProcessDesc', projectTitle);
        onStateMachineComplete();
    })
    .catch(err => { alert("Bir hata oluştu: " + err.message); });
});

// DÜZELTME: Fonksiyon artık 'projectName' parametresi alıyor ve tüm türler için polling yapıyor.
function pollForGraphs(type, frameId, descId, projectName) {
    const frame = document.getElementById(frameId);
    const desc = document.getElementById(descId);

    if (!projectName) {
        console.error("pollForGraphs çağrılırken proje adı eksik!");
        if(desc) desc.textContent = "Hata: Proje adı belirtilmedi.";
        return;
    }

    if (desc) desc.textContent = "Grafik oluşturuluyor, lütfen bekleyin...";

    let attempts = 0;
    const maxAttempts = 20; // 40 saniye (20 * 2000ms)
    const interval = setInterval(() => {
        // DÜZELTME: fetch URL'ine 'project_name' parametresi eklendi.
        fetch(`/graph/get-graph?type=${type}&project_name=${encodeURIComponent(projectName)}`, { method: "HEAD", cache: "no-cache" })
        .then(res => {
            if (res.ok) {
                // DÜZELTME: src'ye de 'project_name' ve cache-buster ekleniyor.
                frame.src = `/graph/get-graph?type=${type}&project_name=${encodeURIComponent(projectName)}&t=${new Date().getTime()}`;
                if(descId) document.getElementById(descId).textContent = "İşlenmiş veri görüntüleniyor";
                clearInterval(interval);
            } else {
                attempts++;
                if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    if(descId) document.getElementById(descId).textContent = `İşlenmiş grafik yüklenemedi (${res.status})`;
                }
            }
        })
        .catch(err => {
            console.error("Polling fetch error:", err);
            attempts++;
            if (attempts >= maxAttempts) {
                clearInterval(interval);
                if(descId) document.getElementById(descId).textContent = "Grafik yükleme hatası.";
            }
        });
    }, 2000);
}

// YENİ: Seçili işlemleri ve parametrelerini toplayan yardımcı fonksiyon
function getSelectedProcesses() {
    const selectedProcesses = [];
    const checkboxes = document.querySelectorAll('.process-controls input[type="checkbox"]:checked');

    checkboxes.forEach(checkbox => {
        const processName = checkbox.value;
        const processObj = { name: processName };
        // Bu kısım, "addProcessBtn" içindeki switch-case mantığının aynısıdır.
        // Kod tekrarını önlemek için bu mantık buraya taşındı.
        // ... (switch-case mantığını buraya ekleyebilirsiniz veya daha modüler hale getirebilirsiniz)
        selectedProcesses.push(processObj);
    });
    
    if (selectedProcesses.length === 0) {
        alert("Lütfen en az bir işlem seçin.");
        return null;
    }
    return selectedProcesses;
}

// YENİ: Debounce yardımcı fonksiyonu
function debounce(func, delay) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), delay);
    };
}

/*=============== DOM YÜKLENDİĞİNDE ÇALIŞACAK KODLAR (PANEL & WEBSOCKET) ===============*/
document.addEventListener("DOMContentLoaded", function () {
    
    // --- Helper Panel İşlevselliği ---
    const helperPanel = document.getElementById("helper-panel");
    const helperClose = document.getElementById("helper-close");
    const helperExpand = document.getElementById("helper-expand");
    const tablinks = document.querySelectorAll(".tablink");
    
    helperPanel.addEventListener("click", (e) => {
        if (!helperPanel.classList.contains("expanded")) {
            helperPanel.classList.add("expanded");
            e.stopPropagation();
        }
    });
    
    helperClose.addEventListener("click", (e) => {
        helperPanel.classList.remove("expanded", "fullscreen");
        e.stopPropagation();
    });
    
    helperExpand.addEventListener("click", (e) => {
        helperPanel.classList.toggle("fullscreen");
        const icon = helperExpand.querySelector("i");
        if (helperPanel.classList.contains("fullscreen")) {
            icon.classList.replace("fa-expand", "fa-compress");
            helperExpand.title = "Küçült";
        } else {
            icon.classList.replace("fa-compress", "fa-expand");
            helperExpand.title = "Tam Ekran";
        }
        e.stopPropagation();
    });
    
    tablinks.forEach(tab => {
        tab.addEventListener("click", function(e) {
            const tabName = this.getAttribute("data-tab");
            document.querySelectorAll(".tabcontent").forEach(c => c.classList.remove("active"));
            document.querySelectorAll(".tablink").forEach(b => b.classList.remove('active'));
            document.getElementById(tabName).classList.add("active");
            this.classList.add("active");
            e.stopPropagation();
        });
    });
    
    document.querySelector(".helper-content").addEventListener("click", e => e.stopPropagation());

    // --- WebSocket Dinleyicisi ---
    const socket = io();

    socket.on('connect', () => {
        console.log('WebSocket sunucusuna başarıyla bağlandı! ID:', socket.id);
    });

    socket.on('log_message', (data) => {
        const logContent = document.getElementById('helper-log-content');
        if (logContent && data.log) {
            const newLogLine = document.createTextNode(data.log + '\n');
            logContent.appendChild(newLogLine);
            logContent.scrollTop = logContent.scrollHeight;
        }
    });

    socket.on('disconnect', () => {
        console.log('WebSocket bağlantısı kesildi.');
    });

    // YENİ: Sunucudan gelen uygunluk sonucunu dinle
    socket.on('suitability_result', (data) => {
        console.log('Uygunluk sonucu alındı:', data);
        const scoreElement = document.getElementById('suitability-score'); // Sonucu gösterecek bir element
        if (scoreElement && data.score) {
            scoreElement.textContent = `Uygunluk: ${data.score.toFixed(2)}%`;
            scoreElement.style.color = data.score > 75 ? 'lightgreen' : (data.score > 50 ? 'orange' : 'salmon');
        }
    });

    // YENİ: Anlık uygunluk kontrolü için fonksiyon
    function checkSuitability() {
        const processes = getSelectedProcesses(); // Seçili işlemleri alan fonksiyonunuz
        const projectTitle = document.getElementById("projectTitle").value;
        
        // uploadedFileName'ın daha önce doldurulduğundan emin olun
        if (!uploadedFileName || !projectTitle) {
            console.warn("Uygunluk kontrolü için önce dosya yüklenmeli ve proje adı girilmelidir.");
            return;
        }

        // DÜZELTME: Olayla birlikte context bilgilerini de gönder
        socket.emit('calculate_suitability', { 
            processes: processes,
            project_name: projectTitle,
            file_name: uploadedFileName 
        });
    }

    // YENİ: Debounce edilmiş versiyonu oluştur (500ms gecikmeyle)
    const debouncedCheckSuitability = debounce(checkSuitability, 500);

    // YENİ: İşlem kontrollerindeki her değişikliği dinle
    document.querySelector('.process-controls').addEventListener('input', debouncedCheckSuitability);
    document.querySelector('.process-controls').addEventListener('change', debouncedCheckSuitability);
});

function showLogPanel() {
    document.getElementById('helper-panel').classList.add('expanded');
    document.querySelectorAll('.tablink').forEach(tab => {
        tab.classList.remove('active');
        if (tab.getAttribute('data-tab') === 'log-tab') tab.classList.add('active');
    });
    document.querySelectorAll('.tabcontent').forEach(content => content.classList.remove('active'));
    document.getElementById('log-tab').classList.add('active');
}

function onStateMachineComplete() {
    checkProcessedFileAndToggleButton();
}

document.getElementById("DownloadBtn").addEventListener("click", function() {
    fetch('/download/check-file')
    .then(res => res.json())
    .then(data => {
        if (data.exists) {
            window.location.href = '/download/processed-data';
        } else {
            alert("İşlenmiş veri dosyası bulunamadı.");
        }
    })
    .catch(err => {
        console.error("Hata:", err);
        alert("Bir hata oluştu.");
    });
});
