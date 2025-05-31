/*=============== SHOW MENU ===============*/
const showMenu = (toggleId, navId) => {
  const toggle = document.getElementById(toggleId),
      nav = document.getElementById(navId)

  toggle.addEventListener('click', () => {
      // Add show-menu class to nav menu
      nav.classList.toggle('show-menu')

      // Add show-icon to show and hide the menu icon
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

// Dosya yükleme işlemini güncelle
document.getElementById('hiddenFileInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    // get-head-api ile head verisini al
    fetch('/upload/get-head-api', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.head) {
            // Yardımcı paneli aç ve head verisini yaz
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
            
            // Paneli otomatik aç ve veri tabını aktif et
            helperPanel.classList.add('expanded');
            document.querySelectorAll('.tablink').forEach(tab => {
                tab.classList.remove('active');
                if (tab.getAttribute('data-tab') === 'data-tab') {
                    tab.classList.add('active');
                }
            });
            document.querySelectorAll('.tabcontent').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById('data-tab').classList.add('active');
        }
    });
    
    // Logları güncelle
    fetchAndShowLogs();

    // Önizleme için get-head-api
    fetch('/upload/get-head-api', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.head) {
            showDataPreview(JSON.parse(data.head));
        }
    });

    // Sütunlar için get-columns-api
    fetch('/upload/get-columns-api', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.columns) {
            fillDropdowns(data.columns);
        }
    });
});

function showDataPreview(rows) {
    const previewDiv = document.getElementById('data-preview');
    previewDiv.innerHTML = ''; // Tabloyu tamamen kaldır
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

    // Sütun adlarını datalist'e ekle
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

// Dropdown işlevselliği
const dropdown1 = document.getElementById('dropdown1');
const dropdown2 = document.getElementById('dropdown2');
const dropdown3 = document.getElementById('dropdown3');
const projectTitle = document.getElementById("projectTitle").value;


// Temizleme fonksiyonu
function clearDropdown(dropdown) {
  dropdown.innerHTML = '<option value="">Seçim Yapın</option>';
  dropdown.disabled = false;
}

// Doldurma fonksiyonu
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




// Mobil menü işlevselliği
const navMenu = document.getElementById('nav-menu');
const navToggle = document.getElementById('nav-toggle');
const navClose = document.querySelector('.nav__close');





/*=============== GÖNDER & POLLING ===============*/

document.getElementById("visualizeBtn").addEventListener("click", () => {
  const plotType = document.getElementById("plotType").value;
  const xAxis = document.getElementById("xAxis").value;
  const yAxis = document.getElementById("yAxis").value;
  const projectTitle = document.getElementById("projectTitle").value;

  if (!selectedFile) {
    alert("Lütfen bir dosya seçin.");
    return;
  }

  if (!projectTitle) {
    alert("Proje başlığı boş olamaz.");
    return;
  }
  if(!plotType){
    alert("Lütfen bir grafik türü seçin.");
    return;
  }

  console.log([
    plotType,
    xAxis,
    yAxis,
    projectTitle
  ]);

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("secim1", plotType);
  formData.append("secim2", xAxis);
  formData.append("secim3", yAxis);
  formData.append("secim4", projectTitle);

  fetch(`/upload/${encodeURIComponent(projectTitle)}`, {
    method: "POST",
    body: formData
  })
    .then(response => {
      if (response.ok) {
        // Logları göster
        fetchAndShowLogs();
        return fetch('/state/run-state-machine', {
          method: 'POST',
          body: new URLSearchParams({ mode: 'visualize_only', output_type: 'raw' })
        });
      } else {
        return response.text().then(text => { throw new Error(text); });
      }
    })
    .then(response => {
      if (response.ok) {
        let attempts = 0;
        const maxAttempts = 10; // Daha kısa tut
        const interval = setInterval(() => {
          fetch("/graph/get-graph?type=raw", { method: "HEAD" })
            .then(res => {
              if (res.ok) {
                document.getElementById("beforeFrame").src = "/graph/get-graph?type=raw";
                clearInterval(interval);
              } else {
                attempts++;
                if (attempts >= maxAttempts) {
                  clearInterval(interval);
                  alert("Grafik oluşturulamadı.");
                }
              }
            })
            .catch(err => {
              clearInterval(interval);
              alert("Bir hata oluştu.");
            });
        }, 3000); // 3 saniye aralıkla dene
      } else {
        return response.text().then(text => { throw new Error("State machine başlatılamadı: " + text); });
      }
    })
    .catch(err => {
      alert(err.message || "Bir hata oluştu.");
    });
});

document.getElementById("addProcessBtn").addEventListener("click", () => {
    const selectedProcesses = [];
    const checkboxes = document.querySelectorAll('.process-controls input[type="checkbox"]:checked');

    checkboxes.forEach(checkbox => {
        const processName = checkbox.value;
        const processObj = { name: processName };

        switch(processName) {
            case "FillMissing":
                const fm_columnInput = document.querySelector(`input[name="FillMissing_column"]`);
                const fm_methodSelect = document.querySelector(`select[name="FillMissing_method"]`);
                if (fm_columnInput && fm_columnInput.value) {
                    processObj.column = fm_columnInput.value.trim(); // Python 'column' bekliyor
                }
                if (fm_methodSelect && fm_methodSelect.value) {
                    processObj.method = fm_methodSelect.value; // Python 'method' bekliyor
                }
                break;
                
            case "timeSeriesShift":
                const ts_colInput = document.querySelector(`input[name="timeSeriesShift_param"]`);
                const ts_periodInput = document.querySelector(`input[name="timeSeriesShift_period"]`);
                if (ts_colInput && ts_colInput.value) {
                    processObj.timeSeriesShift_param = ts_colInput.value.trim(); // Python 'timeSeriesShift_param' bekliyor
                }
                if (ts_periodInput && ts_periodInput.value) {
                    const periodValue = parseInt(ts_periodInput.value);
                    if (!isNaN(periodValue)) {
                        processObj.timeSeriesShift_period = periodValue; // Python 'timeSeriesShift_period' bekliyor
                    } else {
                        alert(`${processName} için geçerli bir sayısal periyot değeri giriniz.`);
                        return; 
                    }
                }
                break;
            
            case "addNoise":
                const an_noiseColInput = document.querySelector(`input[name="addNoise_param"]`);
                const an_noiseLevelInput = document.querySelector(`input[name="addNoise_level"]`);
                if (an_noiseColInput && an_noiseColInput.value) {
                    processObj.column = an_noiseColInput.value.trim(); // Python 'column' bekliyor
                }
                if (an_noiseLevelInput && an_noiseLevelInput.value) {
                    processObj.noise_level = parseFloat(an_noiseLevelInput.value); // Python 'noise_level' bekliyor
                }
                break;
                
            case "RemoveHighNullColumns":
                const rhnc_thresholdInput = document.querySelector(`input[name="RemoveHighNullColumns_param"]`);
                if (rhnc_thresholdInput && rhnc_thresholdInput.value) {
                    processObj.RemoveHighNullColumns_param = parseFloat(rhnc_thresholdInput.value); // Python 'RemoveHighNullColumns_param' bekliyor
                }
                break;

            case "combineColumns":
                const cc_paramInput = document.querySelector(`input[name="combineColumns_param"]`);
                const cc_newInput = document.querySelector(`input[name="combineColumns_new"]`);
                if (cc_paramInput && cc_paramInput.value) {
                    processObj.combineColumns_param = cc_paramInput.value.trim(); // Python 'combineColumns_param' bekliyor
                }
                if (cc_newInput && cc_newInput.value) {
                    processObj.combineColumns_new = cc_newInput.value.trim(); // Python 'combineColumns_new' bekliyor
                }
                break;
                
            default:
                // Genel parametre işleme: HTML input adı "ProcessName_param" ise
                // Python da "ProcessName_param" bekliyorsa bu blok çalışır.
                // FilterRows ve logTransform Python tarafında düzeltildiği için bu blok onları da kapsar.
                const paramInput = document.querySelector(`input[name="${processName}_param"]`);
                if (paramInput && paramInput.value) {
                    processObj[`${processName}_param`] = paramInput.value.trim();
                }
                // Parametresiz işlemler (RemoveWhitespace, CleanEmails vb.) için bu blok bir şey eklemez, bu doğru.
        }
        
        selectedProcesses.push(processObj);
    });
    
    if (selectedProcesses.length === 0) {
        alert("Lütfen en az bir işlem seçin.");
        return;
    }
    
    console.log("Gönderilecek işlemler:", selectedProcesses);
    
    const projectTitle = document.getElementById("projectTitle").value;
    if (!projectTitle) {
        alert("Proje başlığı boş olamaz.");
        return;
    }

    fetch('/state/run-state-machine', {
        method: 'POST',
        body: new URLSearchParams({
            mode: 'full_manual',
            output_type: 'refined',
            processes: JSON.stringify(selectedProcesses),
            projectTitle: projectTitle // Bu parametre Python tarafında okunmuyor gibi, gerekliyse eklenmeli.
        })
    })
    .then(response => response.json())
    .then(data => {
        fetchAndShowLogs();
        alert("İşlemler gönderildi ve analiz başladı!");
        pollForGraphs();
        onStateMachineComplete(); // İndirme butonunu kontrol et
    })
    .catch(err => {
        alert("Bir hata oluştu: " + err.message);
    });
});

// Grafikleri kontrol etmek için polling fonksiyonu
function pollForGraphs() {
    // Önce raw grafiği beforeProcessFrame'e ekle
    document.getElementById("beforeProcessFrame").src = "/graph/get-graph?type=raw";
    
    // Refined grafik için polling yap
    let attempts = 0;
    const maxAttempts = 20;
    const interval = setInterval(() => {
        fetch("/graph/get-graph?type=refined", { method: "HEAD" })
        .then(res => {
            if (res.ok) {
                document.getElementById("afterProcessFrame").src = "/graph/get-graph?type=refined";
                document.getElementById("afterProcessDesc").textContent = "İşlenmiş veri görüntüleniyor";
                clearInterval(interval);
            } else {
                attempts++;
                if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    document.getElementById("afterProcessDesc").textContent = "İşlenmiş grafik yüklenemedi (404)";
                }
            }
        })
        .catch(err => {
            attempts++;
            if (attempts >= maxAttempts) {
                clearInterval(interval);
                document.getElementById("afterProcessDesc").textContent = "Grafik yükleme hatası: " + err.message;
            }
        });
    }, 2000); // 2 saniye aralıkla dene
}

// Helper Panel işlevselliği
document.addEventListener("DOMContentLoaded", function () {
    const helperPanel = document.getElementById("helper-panel");
    const helperClose = document.getElementById("helper-close");
    const helperExpand = document.getElementById("helper-expand");
    const tablinks = document.querySelectorAll(".tablink");
    
    // Panel genişletme/daraltma
    helperPanel.addEventListener("click", function (e) {
        if (!helperPanel.classList.contains("expanded")) {
            helperPanel.classList.add("expanded");
            e.stopPropagation();
        }
    });
    
    // Paneli kapat
    helperClose.addEventListener("click", function (e) {
        helperPanel.classList.remove("expanded");
        helperPanel.classList.remove("fullscreen");
        e.stopPropagation();
    });
    
    // Tam ekran yap/küçült
    helperExpand.addEventListener("click", function (e) {
        helperPanel.classList.toggle("fullscreen");
        
        // İkon değişimi
        const icon = helperExpand.querySelector("i");
        if (helperPanel.classList.contains("fullscreen")) {
            icon.classList.remove("fa-expand");
            icon.classList.add("fa-compress");
            helperExpand.title = "Küçült";
        } else {
            icon.classList.remove("fa-compress");
            icon.classList.add("fa-expand");
            helperExpand.title = "Tam Ekran";
        }
        
        e.stopPropagation();
    });
    
    // Tab değiştirme
    tablinks.forEach(tab => {
        tab.addEventListener("click", function(e) {
            const tabName = this.getAttribute("data-tab");
            
            // Tüm tabları gizle
            document.querySelectorAll(".tabcontent").forEach(content => {
                content.classList.remove("active");
            });
            
            // Tüm tab butonlarını pasif yap
            document.querySelectorAll(".tablink").forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Seçilen tabı göster
            document.getElementById(tabName).classList.add("active");
            this.classList.add("active");
            
            e.stopPropagation();
        });
    });
    
    // Panelin içinde tıklama yapıldığında kapanmaması için
    document.querySelector(".helper-content").addEventListener("click", function(e) {
        e.stopPropagation();
    });
});

// Log fetch fonksiyonunu düzelt
function fetchAndShowLogs() {
    fetch('/logs/latest')
        .then(res => res.json())
        .then(data => {
            const logContent = document.getElementById('helper-log-content');
            
            // Her seferinde log içeriğini temizle
            logContent.textContent = '';
            
            if (data.log) {
                // Satır sonlarını doğru şekilde işle
                const formattedLog = data.log.replace(/\\r?\\n/g, '\n');
                logContent.textContent = formattedLog;
            } else {
                logContent.textContent = "Henüz işlem kaydı yok.";
            }
            
            document.getElementById('helper-panel').classList.add('expanded');
            
            // Log tab'ını aktif et
            document.querySelectorAll('.tablink').forEach(tab => {
                tab.classList.remove('active');
                if (tab.getAttribute('data-tab') === 'log-tab') {
                    tab.classList.add('active');
                }
            });
            
            document.querySelectorAll('.tabcontent').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById('log-tab').classList.add('active');
            
            // Otomatik scroll
            logContent.scrollTop = logContent.scrollHeight;
        });
}

// İndirme butonunu kontrol eden fonksiyon



// State machine işlemi bittikten sonra tekrar kontrol etmek için bu fonksiyonu çağırabilirsin
function onStateMachineComplete() {
    checkProcessedFileAndToggleButton();
}

// İndirme butonuna tıklanınca dosya var mı tekrar kontrol et ve indir
document.getElementById("DownloadBtn").addEventListener("click", function() {
    fetch('/download/check-file')
    .then(res => res.json())
    .then(data => {
        if (data.exists) {
            window.location.href = '/download/processed-data';
        } else {
            alert("İşlenmiş veri dosyası bulunamadı. Lütfen önce veri işleme adımını tamamlayın.");
        }
    })
    .catch(err => {
        console.error("Hata:", err);
        alert("Bir hata oluştu. Sayfayı yenileyip tekrar deneyin.");
    });
});

