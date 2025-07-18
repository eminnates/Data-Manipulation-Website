/*=============== ENHANCED INITIALIZATION ===============*/
document.addEventListener('DOMContentLoaded', function() {
    initializeTabInterface();
    initializeUploadArea();
    initializeFormValidation();
    showNotification('Data Manipulation Platform - Hoş geldiniz!', 'info', 5000);
});

function initializeTabInterface() {
    // Add keyboard navigation for tabs
    const tabNavItems = document.querySelectorAll('.tab-nav-item');
    tabNavItems.forEach((tab, index) => {
        tab.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                const newIndex = e.key === 'ArrowLeft' 
                    ? (index - 1 + tabNavItems.length) % tabNavItems.length
                    : (index + 1) % tabNavItems.length;
                tabNavItems[newIndex].focus();
                tabNavItems[newIndex].click();
            }
        });
    });
}

function initializeUploadArea() {
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        // Enhanced drag and drop functionality
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
        
        // Click to upload functionality
        uploadArea.addEventListener('click', function() {
            const hiddenFileInput = document.getElementById('hiddenFileInput');
            if (hiddenFileInput) {
                hiddenFileInput.click();
            }
        });
    }
}

function initializeFormValidation() {
    // Real-time validation for project name input
    const projectNameInput = document.getElementById('projectNameInput');
    if (projectNameInput) {
        projectNameInput.addEventListener('input', function() {
            const value = this.value.trim();
            const isValid = value.length >= 3 && /^[a-zA-Z0-9_\-\s]+$/.test(value);
            
            this.style.borderColor = isValid ? 'rgb(0, 195, 255)' : '#ff4757';
            
            // Show validation message
            let validationMsg = this.parentNode.querySelector('.validation-message');
            if (!validationMsg) {
                validationMsg = document.createElement('div');
                validationMsg.className = 'validation-message';
                validationMsg.style.cssText = 'font-size: 0.8rem; margin-top: 0.25rem; transition: color 0.3s ease;';
                this.parentNode.appendChild(validationMsg);
            }
            
            if (value.length === 0) {
                validationMsg.textContent = '';
            } else if (value.length < 3) {
                validationMsg.textContent = 'Proje adı en az 3 karakter olmalıdır';
                validationMsg.style.color = '#ff4757';
            } else if (!/^[a-zA-Z0-9_\-\s]+$/.test(value)) {
                validationMsg.textContent = 'Sadece harf, rakam, tire ve alt çizgi kullanılabilir';
                validationMsg.style.color = '#ff4757';
            } else {
                validationMsg.textContent = '✓ Geçerli proje adı';
                validationMsg.style.color = '#00ff88';
            }
        });
    }
}

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

// Enhanced file input handler
const hiddenFileInput = document.getElementById("hiddenFileInput");
if (hiddenFileInput) {
  hiddenFileInput.addEventListener("change", function () {
    const file = this.files[0];
    if (file) {
        handleFileSelection(file);
    }
  });
}
    }
  });
}

const glowButton = document.getElementById("glowButton");
if (glowButton) {
  glowButton.addEventListener("click", () => {
    if (hiddenFileInput) {
      hiddenFileInput.click();
    }
  });
}

// Updated file input handler (compatible with new template)
if (hiddenFileInput) {
  hiddenFileInput.addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (!file) return;

    const chunkSize = 5 * 1024; // 5 KB
    const blob = file.slice(0, chunkSize);

    const reader = new FileReader();
    reader.onload = function(e) {
      const text = e.target.result;
      // İlk 10 satırı ayır
      const lines = text.split(/\r?\n/).slice(0, 10).join("\n");

      const payload = JSON.stringify({ sample: lines });

    // get-head-api çağrısı
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

    // get-columns-api çağrısı
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
}


function showDataPreview(rows) {
    const previewDiv = document.getElementById('data-preview');
    if (previewDiv) {
        previewDiv.innerHTML = ''; // Tabloyu tamamen kaldır
    }
}

function fillDropdowns(columns) {
    const xAxis = document.getElementById('xAxis');
    const yAxis = document.getElementById('yAxis');
    if (xAxis && yAxis) {
        xAxis.innerHTML = '';
        yAxis.innerHTML = '';
        columns.forEach(col => {
            xAxis.innerHTML += `<option value="${col}">${col}</option>`;
            yAxis.innerHTML += `<option value="${col}">${col}</option>`;
        });
    }

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

const visualizeBtn = document.getElementById("visualizeBtn");
if (visualizeBtn) {
  visualizeBtn.addEventListener("click", () => {
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
        showLogPanel()
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
}

const addProcessBtn = document.getElementById("addProcessBtn");
if (addProcessBtn) {
  addProcessBtn.addEventListener("click", () => {
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
        showLogPanel()
        alert("İşlemler gönderildi ve analiz başladı!");
        pollForGraphs();
        onStateMachineComplete(); // İndirme butonunu kontrol et
    })
    .catch(err => {
        alert("Bir hata oluştu: " + err.message);
    });
  });
}

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


function showLogPanel() {
    // Log panelini hemen göster ve log tab'ını aktif et
    document.getElementById('helper-panel').classList.add('expanded');
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
}

// İndirme butonunu kontrol eden fonksiyon



// State machine işlemi bittikten sonra tekrar kontrol etmek için bu fonksiyonu çağırabilirsin
function onStateMachineComplete() {
    checkProcessedFileAndToggleButton();
}

// İndirme butonuna tıklanınca dosya var mı tekrar kontrol et ve indir
const downloadBtn = document.getElementById("DownloadBtn");
if (downloadBtn) {
  downloadBtn.addEventListener("click", function() {
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
}

/* =============== WEBSOCKET DİNLEYİCİSİ ===============*/
document.addEventListener("DOMContentLoaded", function () {

    const socket = io();

    socket.on('connect', () => {
        console.log('WebSocket sunucusuna başarıyla bağlandı! ID:', socket.id);
    });

    // Backend'den 'log_message' olayı geldiğinde çalışacak fonksiyon
    socket.on('log_message', (data) => {
        console.log('Yeni log mesajı alındı:', data);
        const logContent = document.getElementById('helper-log-content');

        if (logContent && data.log) {
            const newLogLine = document.createTextNode(data.log + '\n');
            logContent.appendChild(newLogLine);
            logContent.scrollTop = logContent.scrollHeight;
        }
    });

    // Bağlantı kesildiğinde bilgilendir
    socket.on('disconnect', () => {
        console.log('WebSocket bağlantısı kesildi.');
    });
    
    // --- WEBSOCKET DİNLEYİCİSİ SONU ---
});

/*=============== TAB INTERFACE FUNCTIONS ===============*/

// Enhanced Tab switching functionality with animations
function showTab(evt, tabName) {
    // Hide all tab contents with fade out effect
    const tabcontents = document.getElementsByClassName("tab-content");
    for (let i = 0; i < tabcontents.length; i++) {
        if (tabcontents[i].classList.contains("active")) {
            tabcontents[i].style.opacity = '0';
            tabcontents[i].style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                tabcontents[i].classList.remove("active");
            }, 200);
        }
    }
    
    // Remove active class from all tab navigation items
    const tabnavitems = document.getElementsByClassName("tab-nav-item");
    for (let i = 0; i < tabnavitems.length; i++) {
        tabnavitems[i].classList.remove("active");
    }
    
    // Show the selected tab with fade in effect
    setTimeout(() => {
        const selectedTab = document.getElementById(tabName);
        selectedTab.classList.add("active");
        
        // Force a reflow
        selectedTab.offsetHeight;
        
        // Apply fade in animation
        selectedTab.style.opacity = '1';
        selectedTab.style.transform = 'translateY(0)';
        
        // Mark navigation item as active
        evt.currentTarget.classList.add("active");
        
        // Show notification for tab switch
        showNotification(`Sekmede geçiş yapıldı: ${getTabTitle(tabName)}`, 'success');
    }, 200);
}

// Get user-friendly tab title
function getTabTitle(tabName) {
    const titles = {
        'tab-upload': 'Veri Yükleme',
        'tab-info': 'Veri Bilgisi',
        'tab-operations': 'Veri İşlemleri',
        'tab-visualization': 'Veri Görselleştirme'
    };
    return titles[tabName] || tabName;
}

// Enhanced notification system
function showNotification(message, type = 'info', duration = 3000) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i class="ri-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Show notification with animation
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Auto-hide notification
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'check-line',
        'error': 'error-warning-line',
        'warning': 'alert-line',
        'info': 'information-line'
    };
    return icons[type] || 'information-line';
}

// Enhanced progress bar functionality
function updateProgressBar(percentage, containerId = 'progress-container') {
    let progressContainer = document.getElementById(containerId);
    
    if (!progressContainer) {
        progressContainer = document.createElement('div');
        progressContainer.id = containerId;
        progressContainer.innerHTML = `
            <div class="progress-bar">
                <div class="progress-bar-fill" style="width: 0%"></div>
            </div>
        `;
        
        // Add to the active tab
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab) {
            activeTab.appendChild(progressContainer);
        }
    }
    
    const progressFill = progressContainer.querySelector('.progress-bar-fill');
    progressFill.style.width = `${percentage}%`;
    
    if (percentage >= 100) {
        setTimeout(() => {
            progressContainer.remove();
        }, 1000);
    }
}

// Enhanced loading spinner
function showLoadingSpinner(containerId, message = 'İşleme devam ediliyor...') {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const loadingElement = document.createElement('div');
    loadingElement.className = 'loading-overlay';
    loadingElement.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; gap: 1rem; padding: 2rem; background: rgba(30, 30, 40, 0.95); border-radius: 8px; backdrop-filter: blur(10px);">
            <div class="loading-spinner"></div>
            <span style="color: rgba(255, 255, 255, 0.8);">${message}</span>
        </div>
    `;
    loadingElement.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(5px);
        z-index: 1000;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    container.style.position = 'relative';
    container.appendChild(loadingElement);
    
    // Fade in
    setTimeout(() => loadingElement.style.opacity = '1', 10);
    
    return loadingElement;
}

function hideLoadingSpinner(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const loadingElement = container.querySelector('.loading-overlay');
    if (loadingElement) {
        loadingElement.style.opacity = '0';
        setTimeout(() => loadingElement.remove(), 300);
    }
}

// Enhanced Upload area functionality
function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const uploadArea = event.currentTarget;
    uploadArea.classList.remove('dragover');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        handleFileSelection(file);
        showNotification(`Dosya seçildi: ${file.name}`, 'success');
    } else {
        showNotification('Dosya yüklenemedi. Lütfen tekrar deneyin.', 'error');
        uploadArea.classList.add('shake');
        setTimeout(() => uploadArea.classList.remove('shake'), 600);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    
    // Only remove dragover if we're actually leaving the upload area
    if (!event.currentTarget.contains(event.relatedTarget)) {
        event.currentTarget.classList.remove('dragover');
    }
}

// Enhanced file selection handler
function handleFileSelection(file) {
    if (!file) return;
    
    // Validate file type
    const validExtensions = ['csv', 'xlsx', 'xml', 'json'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(fileExtension)) {
        showNotification(`Geçersiz dosya formatı: ${fileExtension}. Desteklenen formatlar: ${validExtensions.join(', ')}`, 'error');
        return;
    }
    
    // Validate file size (max 50MB)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
        showNotification('Dosya boyutu çok büyük. Maksimum 50MB desteklenmektedir.', 'error');
        return;
    }
    
    selectedFile = file;
    
    // Update UI
    updateFileInfo(file);
    
    // Show success feedback
    showNotification(`Dosya başarıyla seçildi: ${file.name}`, 'success');
    
    // Add visual feedback
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.classList.add('pulse');
        setTimeout(() => uploadArea.classList.remove('pulse'), 2000);
    }
}

// Update file information display
function updateFileInfo(file) {
    const fileInfoElement = document.getElementById('file-info');
    if (fileInfoElement) {
        const fileSize = (file.size / 1024 / 1024).toFixed(2);
        fileInfoElement.innerHTML = `
            <div style="background: rgba(79, 195, 247, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid rgb(0, 195, 255);">
                <h4 style="color: rgb(0, 195, 255); margin-bottom: 0.5rem;">Seçili Dosya</h4>
                <p><strong>Ad:</strong> ${file.name}</p>
                <p><strong>Boyut:</strong> ${fileSize} MB</p>
                <p><strong>Tip:</strong> ${file.type || 'Bilinmiyor'}</p>
                <p><strong>Son Değişiklik:</strong> ${new Date(file.lastModified).toLocaleString('tr-TR')}</p>
            </div>
        `;
    }
}

function handleFileSelection(file) {
    selectedFile = file;
    const validExtensions = ['csv', 'xlsx', 'xml', 'json'];
    const fileExtension = file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(fileExtension)) {
        alert("Geçersiz dosya formatı. Lütfen csv, xlsx, xml veya json dosyası seçin.");
        return;
    }

    // Show file info
    const fileInfo = document.getElementById('file-info');
    const fileDetails = document.getElementById('file-details');
    
    fileDetails.innerHTML = `
        <div style="background: rgba(255,255,255,0.05); border-radius: 8px; padding: 1rem;">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                <i class="ri-file-line" style="font-size: 2rem; color: rgb(0, 195, 255);"></i>
                <div>
                    <div style="font-weight: 600; color: white;">${file.name}</div>
                    <div style="color: rgba(255, 255, 255, 0.6);">${(file.size / 1024).toFixed(2)} KB</div>
                </div>
            </div>
            <div style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">
                📄 Format: ${fileExtension.toUpperCase()}
            </div>
        </div>
    `;
    
    fileInfo.style.display = 'block';
}

// Enhanced Upload button functionality
function uploadFile() {
    if (!selectedFile) {
        showNotification("Lütfen önce bir dosya seçin.", 'warning');
        const uploadArea = document.querySelector('.upload-area');
        if (uploadArea) {
            uploadArea.classList.add('shake');
            setTimeout(() => uploadArea.classList.remove('shake'), 600);
        }
        return;
    }
    
    const projectName = document.getElementById('projectNameInput').value.trim();
    if (!projectName) {
        showNotification("Lütfen proje adını girin.", 'warning');
        document.getElementById('projectNameInput').focus();
        return;
    }
    
    // Show loading state
    const loadingOverlay = showLoadingSpinner('tab-upload', 'Dosya yükleniyor...');
    updateProgressBar(0);
    
    // Simulate upload progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 30;
        if (progress > 90) progress = 90;
        updateProgressBar(progress);
    }, 200);
    
    // Process file upload
    const chunkSize = 5 * 1024; // 5 KB
    const blob = selectedFile.slice(0, chunkSize);
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        const lines = text.split(/\r?\n/).slice(0, 10).join("\n");
        const payload = JSON.stringify({ sample: lines });
        
        // Update data info and switch to data info tab
        fetch('/upload/get-head-api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: payload
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.head) {
                clearInterval(progressInterval);
                updateProgressBar(100);
                
                updateDataInfo(data);
                
                // Hide loading and show success
                hideLoadingSpinner('tab-upload');
                showNotification('Dosya başarıyla yüklendi!', 'success');
                
                // Auto-switch to data info tab with delay
                setTimeout(() => {
                    document.querySelector('[onclick="showTab(event, \'tab-info\')"]').click();
                }, 1000);
            } else {
                throw new Error('Dosya işlenemedi');
            }
        })
        .catch(err => {
            clearInterval(progressInterval);
            hideLoadingSpinner('tab-upload');
            console.error("Upload error:", err);
            showNotification(`Yükleme hatası: ${err.message}`, 'error');
        });
        
        // Get columns for dropdowns
        fetch('/upload/get-columns-api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: payload
        })
        .then(response => response.json())
        .then(data => {
            if (data.columns) {
                updateColumnSelections(data.columns);
            }
        })
        .catch(err => console.error("Columns error:", err));
    };
    
    reader.readAsText(blob);
}

function clearFile() {
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('file-info').style.display = 'none';
    document.getElementById('projectNameInput').value = '';
}

// Update data info tab with file statistics
function updateDataInfo(data) {
    const rows = JSON.parse(data.head);
    if (rows && rows.length > 0) {
        const columns = Object.keys(rows[0]);
        
        // Update basic stats
        document.getElementById('total-rows').textContent = rows.length + '+';
        document.getElementById('total-columns').textContent = columns.length;
        document.getElementById('file-size').textContent = (selectedFile.size / 1024).toFixed(2) + ' KB';
        
        // Simulate other stats (in a real app, these would come from backend)
        document.getElementById('missing-values').textContent = '0';
        document.getElementById('numeric-columns').textContent = '0';
        document.getElementById('categorical-columns').textContent = columns.length;
        document.getElementById('avg-skewness').textContent = '0.12';
        document.getElementById('avg-std').textContent = '1.45';
        document.getElementById('avg-variance').textContent = '2.1';
        
        // Update data preview table
        const previewTable = document.getElementById('data-preview-table');
        let table = '<table style="width:100%; color:white; border-collapse:collapse; margin-top: 1rem;">';
        table += '<tr>' + columns.map(col => `<th style="border: 1px solid rgba(255,255,255,0.2); padding: 8px; background: rgba(0,195,255,0.2);">${col}</th>`).join('') + '</tr>';
        rows.slice(0, 5).forEach(row => {
            table += '<tr>' + columns.map(col => `<td style="border: 1px solid rgba(255,255,255,0.2); padding: 8px;">${row[col] || '-'}</td>`).join('') + '</tr>';
        });
        table += '</table>';
        
        previewTable.innerHTML = `
            <h3 style="color: rgb(0, 195, 255); margin-bottom: 1rem;">Veri Önizleme</h3>
            <div style="background: rgba(255,255,255,0.05); border-radius: 8px; padding: 1rem; overflow-x: auto;">
                ${table}
            </div>
        `;
    }
}

// Update column selections in operations tab
function updateColumnSelections(columns) {
    // Update visualization dropdowns
    const xAxis = document.getElementById('xAxis');
    const yAxis = document.getElementById('yAxis');
    
    xAxis.innerHTML = '<option value="">X Ekseni Seç</option>';
    yAxis.innerHTML = '<option value="">Y Ekseni Seç</option>';
    
    columns.forEach(col => {
        xAxis.innerHTML += `<option value="${col}">${col}</option>`;
        yAxis.innerHTML += `<option value="${col}">${col}</option>`;
    });
    
    // Update operation column selectors
    const columnSelectors = document.querySelectorAll('.column-dropdown');
    columnSelectors.forEach(select => {
        const currentOptions = select.innerHTML;
        let newOptions = '';
        
        if (currentOptions.includes('📋 Tüm')) {
            newOptions = select.querySelector('[value="all"]').outerHTML;
        }
        
        columns.forEach(col => {
            newOptions += `<option value="${col}">📄 ${col}</option>`;
        });
        
        select.innerHTML = newOptions;
    });
}

// Advanced operation toggle
function toggleAdvancedOperation(element, operationType) {
    const isExpanded = element.classList.contains('expanded');
    const details = document.getElementById(`${operationType}-details`);
    
    // Close all other expanded operations
    document.querySelectorAll('.operation-item.expanded').forEach(item => {
        if (item !== element) {
            item.classList.remove('expanded');
            const otherDetails = item.nextElementSibling;
            if (otherDetails && otherDetails.classList.contains('operation-details')) {
                otherDetails.style.display = 'none';
            }
        }
    });
    
    if (isExpanded) {
        element.classList.remove('expanded', 'selected');
        details.style.display = 'none';
    } else {
        element.classList.add('expanded', 'selected');
        details.style.display = 'block';
    }
}

// Simple operation toggle
function toggleOperation(element) {
    element.classList.toggle('selected');
}

// Preview functionality
function togglePreview() {
    const content = document.getElementById('affected-values-content');
    const icon = document.getElementById('preview-icon');
    const text = document.getElementById('preview-text');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.classList.remove('ri-eye-line');
        icon.classList.add('ri-eye-off-line');
        text.textContent = 'Önizlemeyi Gizle';
    } else {
        content.style.display = 'none';
        icon.classList.remove('ri-eye-off-line');
        icon.classList.add('ri-eye-line');
        text.textContent = 'Önizlemeyi Göster';
    }
}

function togglePreviewGeneric(operationType) {
    const content = document.getElementById(`${operationType}-values-content`);
    const icon = document.getElementById(`${operationType}-preview-icon`);
    const text = document.getElementById(`${operationType}-preview-text`);
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.classList.remove('ri-eye-line');
        icon.classList.add('ri-eye-off-line');
        text.textContent = 'Önizlemeyi Gizle';
    } else {
        content.style.display = 'none';
        icon.classList.remove('ri-eye-off-line');
        icon.classList.add('ri-eye-line');
        text.textContent = 'Önizlemeyi Göster';
    }
}

// Operations functionality
function applyOperations() {
    const selectedOps = document.querySelectorAll('.operation-item.selected');
    if (selectedOps.length === 0) {
        alert('Lütfen en az bir işlem seçin.');
        return;
    }
    
    alert(`${selectedOps.length} işlem uygulanacak. Bu özellik geliştirme aşamasındadır.`);
}

function resetOperations() {
    document.querySelectorAll('.operation-item.selected').forEach(item => {
        item.classList.remove('selected', 'expanded');
    });
    document.querySelectorAll('.operation-details').forEach(detail => {
        detail.style.display = 'none';
    });
}

// Visualization functionality
function generateVisualization() {
    const plotType = document.getElementById('plotType').value;
    const xAxis = document.getElementById('xAxis').value;
    const yAxis = document.getElementById('yAxis').value;
    
    if (!plotType || !xAxis || !yAxis) {
        alert('Lütfen tüm grafik parametrelerini seçin.');
        return;
    }
    
    // This would integrate with existing visualization logic
    alert('Görselleştirme özelliği mevcut sistem ile entegre edilecek.');
}

function exportChart() {
    alert('Grafik indirme özelliği geliştirme aşamasındadır.');
}

});

// Enhanced upload area interactions
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        uploadArea.addEventListener('dragenter', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            if (!uploadArea.contains(e.relatedTarget)) {
                uploadArea.classList.remove('drag-over');
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelection(e.target.files[0]);
            }
        });
    }
});
