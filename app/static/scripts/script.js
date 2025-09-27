// Navigation Toggle
const navToggle = document.getElementById('nav-toggle');
const navMenu = document.getElementById('nav-menu');

if (navToggle) {
    navToggle.addEventListener('click', () => {
        navMenu.classList.toggle('show-menu');
        
        const navBurger = navToggle.querySelector('.nav__burger');
        const navClose = navToggle.querySelector('.nav__close');
        
        if (navMenu.classList.contains('show-menu')) {
            navBurger.style.opacity = '0';
            navClose.style.opacity = '1';
        } else {
            navBurger.style.opacity = '1';
            navClose.style.opacity = '0';
        }
    });
}

// Close menu when clicking on nav links
const navLinks = document.querySelectorAll('.nav__link');
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('show-menu');
        const navBurger = navToggle.querySelector('.nav__burger');
        const navClose = navToggle.querySelector('.nav__close');
        navBurger.style.opacity = '1';
        navClose.style.opacity = '0';
    });
});

// WebSocket bağlantısı
const socket = io('http://127.0.0.1:5000');
let currentAnalysisProject = null;

// WebSocket event listeners
socket.on('connect', function() {
    console.log('WebSocket bağlantısı kuruldu');
    
    // Bağlantı kurulduktan sonra mevcut projenin durumunu kontrol et
    if (currentAnalysisProject) {
        console.log('Checking status for current project:', currentAnalysisProject);
        setTimeout(() => {
            socket.emit('get_analysis_status', {
                project_name: currentAnalysisProject
            });
        }, 1000);
    }
});

socket.on('disconnect', function() {
    console.log('WebSocket bağlantısı kesildi');
    // Modal varsa kapat
    const modal = document.getElementById('analysis-modal');
    if (modal) modal.remove();
});

socket.on('connect_error', function(error) {
    console.error('WebSocket bağlantı hatası:', error);
    // Modal varsa kapat
    const modal = document.getElementById('analysis-modal');
    if (modal) modal.remove();
    alert('Sunucu bağlantısında hata oluştu. Sayfayı yenileyin.');
});

socket.on('error', function(error) {
    console.error('WebSocket hatası:', error);
    // Modal varsa kapat
    const modal = document.getElementById('analysis-modal');
    if (modal) modal.remove();
});

socket.on('data_analysis_status', function(data) {
    console.log('Analiz durumu:', data);
    updateAnalysisProgress(data);
});

socket.on('data_analysis_complete', function(data) {
    console.log('Analiz tamamlandı:', data);
    handleAnalysisComplete(data);
});

socket.on('data_analysis_error', function(data) {
    console.error('Analiz hatası:', data);
    handleAnalysisError(data);
});

socket.on('suitability_result', function(data) {
    console.log('Suitability result:', data);
    handleSuitabilityResult(data);
});

socket.on('analysis_status_response', function(data) {
    console.log('Analysis status response:', data);
});

socket.on('column_names_result', function(data) {
    console.log('Column names result:', data);
    handleColumnNamesResult(data);
});

// Sütun adlarını dinamik olarak yükle
function requestColumnNames(projectName, fileName) {
    if (!projectName || !fileName) {
        console.warn('Project name or file name is missing');
        return;
    }
    
    console.log('Requesting column names for:', projectName, fileName);
    socket.emit('get_column_names', {
        project_name: projectName,
        file_name: fileName
    });
}

// Sütun adları sonucunu işle
function handleColumnNamesResult(data) {
    console.log('Handling column names result:', data);
    
    if (data.error) {
        console.error('Column names error:', data.error);
        // Hata durumunda varsayılan sütunları göster
        populateColumnDropdowns([]);
        return;
    }
    
    if (data.columns && Array.isArray(data.columns)) {
        console.log('Updating column dropdowns with', data.columns.length, 'columns');
        populateColumnDropdowns(data.columns);
        
        // Proje bilgilerini güncelle
        window.currentProjectColumns = data.columns;
        window.currentProjectInfo = {
            project_name: data.project_name,
            file_name: data.file_name,
            total_rows: data.total_rows
        };
    }
}

// Tüm sütun dropdownlarını güncelle
function populateColumnDropdowns(columns) {
    const columnDropdownIds = [
        'whitespace-columns',
        'duplicate-columns', 
        'special-chars-columns', 
        'case-normalize-columns',
        'delete-columns-columns', 
        'data-types-columns', 
        'categorical-columns', 
        'date-format-columns',
        'normalization-columns', 
        'outliers-columns', 
        'range-filter-columns'
    ];
    
    columnDropdownIds.forEach(dropdownId => {
        const dropdown = document.getElementById(dropdownId);
        if (dropdown) {
            updateColumnDropdown(dropdown, columns);
        }
    });
}

// Tek bir dropdown'u güncelle
function updateColumnDropdown(dropdown, columns) {
    // Mevcut seçimleri sakla
    const previousSelections = Array.from(dropdown.selectedOptions).map(option => option.value);
    
    // Dropdown'u temizle
    dropdown.innerHTML = '';
    
    // "Tüm Sütunlar" seçeneğini ekle
    const allOption = document.createElement('option');
    allOption.value = 'all';
    allOption.textContent = 'Tüm Sütunlar';
    dropdown.appendChild(allOption);
    
    // Gerçek sütunları ekle
    columns.forEach(column => {
        const option = document.createElement('option');
        option.value = column.name;
        
        // Sütun tipine göre ikon ekle
        let icon = '📄'; // Varsayılan
        if (column.is_numeric) {
            icon = '📊';
        } else if (column.is_string) {
            icon = '📄';
        }
        
        // Sütun bilgilerini göster
        const nullInfo = column.null_count > 0 ? ` (${column.null_count} null)` : '';
        const uniqueInfo = column.unique_count < 50 ? ` (${column.unique_count} unique)` : '';
        
        option.textContent = `${icon} ${column.name}${nullInfo}${uniqueInfo}`;
        dropdown.appendChild(option);
    });
    
    // Eğer önceki seçimler varsa, geçerli olanları yeniden seç
    if (previousSelections.length > 0) {
        previousSelections.forEach(value => {
            const option = dropdown.querySelector(`option[value="${value}"]`);
            if (option) {
                option.selected = true;
            }
        });
    }
    
    console.log(`Updated dropdown ${dropdown.id} with ${columns.length} columns`);
}

// Dosya yüklendikten sonra sütun adlarını yükle
function loadColumnsAfterUpload(projectName, fileName) {
    // Kısa bir bekleme sonrası sütun adlarını yükle
    setTimeout(() => {
        requestColumnNames(projectName, fileName);
    }, 1000); // 1 saniye bekle ki dosya işlensin
}

// Analiz progress gösterimi
function updateAnalysisProgress(data) {
    if (data.status === 'started') {
        showAnalysisModal();
        updateProgressBar(0, data.message);
        updateAnalysisStatusWithProgress('Analiz başlatıldı...', 0);
    } else if (data.status === 'progress') {
        const progress = (data.step / data.total_steps) * 100;
        updateProgressBar(progress, data.message);
        updateAnalysisStatusWithProgress(data.message, Math.round(progress));
    }
}

function showAnalysisModal() {
    // Mevcut modal varsa kapat
    const existingModal = document.getElementById('analysis-modal');
    if (existingModal) existingModal.remove();
    
    // Analiz modal'ını göster
    const modal = document.createElement('div');
    modal.id = 'analysis-modal';
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center;
        z-index: 10000;
    `;
    
    modal.innerHTML = `
        <div style="background: hsl(221, 35%, 16%); padding: 2rem; border-radius: 12px; text-align: center; color: white; min-width: 400px; position: relative;">
            <button onclick="closeAnalysisModal()" style="position: absolute; top: 10px; right: 15px; background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer; opacity: 0.7;">×</button>
            <h3 style="color: rgb(0, 195, 255); margin-bottom: 1rem;">Veri Analizi</h3>
            <div id="analysis-progress-bar" style="background: rgba(255,255,255,0.1); height: 20px; border-radius: 10px; margin: 1rem 0; overflow: hidden;">
                <div id="analysis-progress-fill" style="background: rgb(0, 195, 255); height: 100%; width: 0%; transition: width 0.3s ease;"></div>
            </div>
            <p id="analysis-status-text">Veri analizi başlatılıyor...</p>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 30 saniye sonra otomatik kapanma
    setTimeout(() => {
        const modal = document.getElementById('analysis-modal');
        if (modal) {
            modal.remove();
            alert('Analiz çok uzun sürdü. Lütfen sayfayı yenileyin ve tekrar deneyin.');
        }
    }, 30000);
}

// Modal'ı kapatma fonksiyonu
function closeAnalysisModal() {
    const modal = document.getElementById('analysis-modal');
    if (modal) modal.remove();
}

function updateProgressBar(progress, message) {
    const fillBar = document.getElementById('analysis-progress-fill');
    const statusText = document.getElementById('analysis-status-text');
    
    if (fillBar) fillBar.style.width = progress + '%';
    if (statusText) statusText.textContent = message;
}

function handleAnalysisComplete(data) {
    // Progress modal'ını kapat
    const modal = document.getElementById('analysis-modal');
    if (modal) modal.remove();
    
    // Analiz sonuçlarını göster
    alert('Veri analizi tamamlandı! Sonuçlar Veri Bilgisi sekmesinde görüntülenebilir.');
    
    // Dosya yükleme alanındaki analiz durumunu güncelle
    updateAnalysisStatusInFileDetails('Tamamlandı', 'green');
    
    // Veri Bilgisi sekmesini aktif et
    const dataInfoTab = document.querySelector('[onclick*="tab-info"]');
    if (dataInfoTab) {
        dataInfoTab.click();
    }
    
    // Analiz sonuçlarını saklayalım
    window.lastAnalysisResults = data.results;
    
    // Veri bilgilerini güncelle
    if (data.results) {
        updateDataInfoFromAnalysis(data.results);
    }
}

function handleAnalysisError(data) {
    const modal = document.getElementById('analysis-modal');
    if (modal) modal.remove();
    
    // Dosya yükleme alanındaki analiz durumunu güncelle
    updateAnalysisStatusInFileDetails('Hata oluştu', 'red');
    
    // WebSocket bağlantı hatalarını da kontrol et
    const errorMessage = data.message || 'Bilinmeyen hata oluştu';
    console.error('Analysis error:', errorMessage);
    
    alert('Veri analizi sırasında hata oluştu: ' + errorMessage);
}

function handleSuitabilityResult(data) {
    console.log('Suitability calculation result:', data);
    console.log('Looking for loading elements...');
    
    // Reset any loading states - look for elements that are currently calculating
    const loadingElements = document.querySelectorAll('[data-calculating="true"]');
    console.log('Found loading elements with data-calculating:', loadingElements.length);
    
    loadingElements.forEach(element => {
        console.log('Updating element:', element);
        element.removeAttribute('data-calculating');
        if (data.error) {
            element.innerHTML = 'Hesaplanamadı';
            element.style.color = '#ff6b6b';
        } else {
            const affectedRows = data['Total affected rows'] || 0;
            element.innerHTML = affectedRows.toLocaleString();
            element.style.color = affectedRows > 0 ? '#51cf66' : '#ffd43b';
        }
    });
    
    // Fallback - also check for any element that still shows loading
    const allLoadingElements = document.querySelectorAll('[id$="-affected-count"]');
    console.log('Found all affected count elements:', allLoadingElements.length);
    
    // Also check for the main "affected-count" element
    const mainAffectedElement = document.getElementById('affected-count');
    if (mainAffectedElement) {
        console.log('Found main affected-count element:', mainAffectedElement.innerHTML);
        if (mainAffectedElement.innerHTML.includes('Hesaplanıyor') || mainAffectedElement.innerHTML.includes('loader-line')) {
            console.log('Updating main affected-count element');
            if (data.error) {
                mainAffectedElement.innerHTML = 'Hesaplanamadı';
                mainAffectedElement.style.color = '#ff6b6b';
            } else {
                const affectedRows = data['Total affected rows'] || 0;
                mainAffectedElement.innerHTML = affectedRows.toLocaleString();
                mainAffectedElement.style.color = affectedRows > 0 ? '#51cf66' : '#ffd43b';
            }
        }
    }
    
    allLoadingElements.forEach(element => {
        console.log('Checking element:', element.id, 'content:', element.innerHTML);
        if (element.innerHTML.includes('Hesaplanıyor') || element.innerHTML.includes('loader-line')) {
            console.log('Updating fallback element:', element.id);
            if (data.error) {
                element.innerHTML = 'Hesaplanamadı';
                element.style.color = '#ff6b6b';
            } else {
                const affectedRows = data['Total affected rows'] || 0;
                element.innerHTML = affectedRows.toLocaleString();
                element.style.color = affectedRows > 0 ? '#51cf66' : '#ffd43b';
            }
        }
    });
    
    // Show error message if any
    if (data.error) {
        console.error('Suitability calculation error:', data.error);
        // You can show a toast notification here instead of alert
        // showToast('Uygunluk hesaplanırken hata: ' + data.error, 'error');
    }
}

function updateDataInfoFromAnalysis(results) {
    // Temel bilgileri güncelle
    if (results.basic_info) {
        const basicInfo = results.basic_info;
        document.getElementById('total-rows').textContent = basicInfo.total_rows.toLocaleString();
        document.getElementById('total-columns').textContent = basicInfo.total_columns;
        document.getElementById('file-size').textContent = basicInfo.file_size + ' MB';
        document.getElementById('missing-values').textContent = basicInfo.missing_values;
        document.getElementById('numeric-columns').textContent = basicInfo.numeric_columns_count;
        document.getElementById('categorical-columns').textContent = basicInfo.categorical_columns_count;
    }
    
    // İstatistiksel özellikleri güncelle
    if (results.statistical_features) {
        const statFeatures = results.statistical_features;
        document.getElementById('avg-skewness').textContent = statFeatures.avg_skewness;
        document.getElementById('avg-std').textContent = statFeatures.avg_std;
        document.getElementById('avg-variance').textContent = statFeatures.avg_variance;
        document.getElementById('correlation-status').textContent = statFeatures.correlation_status;
    }
    
    // Sütun istatistiklerini güncelle
    if (results.column_statistics) {
        updateColumnStatisticsFromAnalysis(results.column_statistics);
    }
    
    // Veri önizlemesini güncelle
    if (results.data_preview) {
        updateDataPreview(results.data_preview);
    }
}

// Veri önizleme fonksiyonu
function updateDataPreview(previewData) {
    const previewContainer = document.getElementById('data-preview-table');
    
    if (!previewData || !previewData.columns || !previewData.data) {
        return;
    }
    
    let tableHTML = `
        <h3 style="color: rgb(0, 195, 255); margin-bottom: 1rem;">Veri Önizleme</h3>
        <div class="data-preview-container">
            <div style="margin-bottom: 1rem; padding: 1rem; background: rgba(0, 195, 255, 0.1); border-radius: 8px;">
                <div style="display: flex; gap: 2rem; font-size: 0.9rem; color: rgba(255,255,255,0.9);">
                    <span><i class="ri-table-line"></i> ${previewData.total_rows} satır</span>
                    <span><i class="ri-layout-column-line"></i> ${previewData.columns.length} sütun</span>
                    <span><i class="ri-eye-line"></i> İlk ${previewData.data.length} satır görüntüleniyor</span>
                </div>
            </div>
            
            <div style="overflow-x: auto; border-radius: 8px;">
                <table class="data-table">
                    <thead>
                        <tr>`;
    
    // Sütun başlıklarını ekle
    previewData.columns.forEach(column => {
        tableHTML += `<th><i class="ri-table-2"></i> ${column}</th>`;
    });
    
    tableHTML += `</tr></thead><tbody>`;
    
    // Veri satırlarını ekle
    previewData.data.forEach((row, index) => {
        tableHTML += `<tr>`;
        previewData.columns.forEach(column => {
            const value = row[column];
            const displayValue = value !== null && value !== undefined ? 
                (typeof value === 'number' ? Number(value).toLocaleString() : String(value)) : 
                '<span style="color: rgba(255,255,255,0.4); font-style: italic;">null</span>';
            tableHTML += `<td>${displayValue}</td>`;
        });
        tableHTML += `</tr>`;
    });
    
    tableHTML += `
                    </tbody>
                </table>
            </div>
            
            ${previewData.data.length < previewData.total_rows ? 
                `<div style="text-align: center; margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; color: rgba(255,255,255,0.7);">
                    <i class="ri-information-line"></i> Tablonun tamamını görmek için veri işleme araçlarını kullanabilirsiniz
                </div>` : ''
            }
        </div>
    `;
    
    previewContainer.innerHTML = tableHTML;
}

function updateColumnStatisticsFromAnalysis(columnStats) {
    const columnStatsDiv = document.getElementById('column-statistics');
    
    // Veri kontrolü
    if (!columnStats || !Array.isArray(columnStats) || columnStats.length === 0) {
        columnStatsDiv.innerHTML = `
            <div style="text-align: center; color: rgba(255,255,255,0.6); padding: 2rem;">
                Sütun istatistikleri bulunamadı.
            </div>
        `;
        return;
    }
    
    let statsHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem;">
    `;
    
    columnStats.forEach((stat, index) => {
        // Stat verilerini güvenli kontrol et
        if (!stat || typeof stat !== 'object') {
            return;
        }
        
        try {
            // Grafik verisi için sample data oluştur
            const chartData = generateSampleChartData(stat);
            
            // Güvenli değer okuma
            const columnName = stat.column_name || `Sütun ${index + 1}`;
            const mean = (typeof stat.mean === 'number' && !isNaN(stat.mean)) ? stat.mean.toFixed(2) : 'N/A';
            const std = (typeof stat.std === 'number' && !isNaN(stat.std)) ? stat.std.toFixed(2) : 'N/A';
            const min = (typeof stat.min === 'number' && !isNaN(stat.min)) ? stat.min.toFixed(2) : 'N/A';
            const max = (typeof stat.max === 'number' && !isNaN(stat.max)) ? stat.max.toFixed(2) : 'N/A';
            const median = (typeof stat.median === 'number' && !isNaN(stat.median)) ? stat.median.toFixed(2) : 'N/A';
            const variance = (typeof stat.variance === 'number' && !isNaN(stat.variance)) ? stat.variance.toFixed(2) : 'N/A';
            const skewness = (typeof stat.skewness === 'number' && !isNaN(stat.skewness)) ? stat.skewness.toFixed(3) : 'N/A';
            const kurtosis = (typeof stat.kurtosis === 'number' && !isNaN(stat.kurtosis)) ? stat.kurtosis.toFixed(3) : 'N/A';
            
            statsHTML += `
                <div class="column-stat-card" data-column="${columnName}">
                    <div class="stat-header">
                        <div class="stat-icon"><i class="ri-bar-chart-line"></i></div>
                        <div class="stat-column-name">${columnName}</div>
                    </div>
                    <div class="stat-grid">
                        <div class="stat-item">
                            <span class="stat-label">Ortalama</span>
                            <span class="stat-value">${mean}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Std. Sapma</span>
                            <span class="stat-value">${std}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Minimum</span>
                            <span class="stat-value">${min}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Maksimum</span>
                            <span class="stat-value">${max}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Medyan</span>
                            <span class="stat-value">${median}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Varyans</span>
                            <span class="stat-value">${variance}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Çarpıklık</span>
                            <span class="stat-value" style="color: ${skewness !== 'N/A' && Math.abs(parseFloat(skewness)) > 1 ? '#ff6b6b' : '#51cf66'};">${skewness}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Basıklık</span>
                            <span class="stat-value">${kurtosis}</span>
                        </div>
                    </div>
                    
                    <!-- Hover Chart Overlay -->
                    <div class="column-chart-overlay">
                        <div class="chart-title">
                            <i class="ri-bar-chart-2-line"></i>
                            ${columnName} Dağılım Grafiği
                        </div>
                        <div class="mini-chart">
                            <div class="chart-bars">
                                ${chartData.bars.map((height, i) => `
                                    <div class="chart-bar" style="height: ${height}%;" 
                                         title="Değer: ${chartData.values[i]}, Frekans: ${chartData.frequencies[i]}">
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="chart-info">
                            <div class="chart-info-item">
                                <span>Mod:</span>
                                <span>${chartData.mode}</span>
                            </div>
                            <div class="chart-info-item">
                                <span>Aralık:</span>
                                <span>${chartData.range}</span>
                            </div>
                            <div class="chart-info-item">
                                <span>Q1:</span>
                                <span>${chartData.q1}</span>
                            </div>
                            <div class="chart-info-item">
                                <span>Q3:</span>
                                <span>${chartData.q3}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Sütun istatistiği oluşturulurken hata:', error, stat);
            // Hata durumunda basit kart göster
            statsHTML += `
                <div class="column-stat-card">
                    <div class="stat-header">
                        <div class="stat-icon"><i class="ri-alert-line"></i></div>
                        <div class="stat-column-name">Hata: ${stat.column_name || 'Bilinmeyen Sütun'}</div>
                    </div>
                    <div style="padding: 1rem; text-align: center; color: rgba(255,255,255,0.6);">
                        Bu sütun için istatistikler hesaplanamadı.
                    </div>
                </div>
            `;
        }
    });
    
    statsHTML += `</div>`;
    columnStatsDiv.innerHTML = statsHTML;
}

// Sütun için sample grafik verisi oluştur
function generateSampleChartData(stat) {
    // Güvenli değer atama
    const min = (typeof stat.min === 'number' && !isNaN(stat.min)) ? stat.min : 0;
    const max = (typeof stat.max === 'number' && !isNaN(stat.max)) ? stat.max : 100;
    const mean = (typeof stat.mean === 'number' && !isNaN(stat.mean)) ? stat.mean : 50;
    const std = (typeof stat.std === 'number' && !isNaN(stat.std) && stat.std > 0) ? stat.std : 15;
    
    // Min ve max'in aynı olma durumunu kontrol et
    if (max <= min) {
        return {
            bars: Array(20).fill(50),
            values: Array(20).fill(min.toFixed(1)),
            frequencies: Array(20).fill(10),
            range: '0.00',
            q1: min.toFixed(2),
            q3: min.toFixed(2),
            mode: min.toFixed(2)
        };
    }
    
    // Normal dağılım benzeri histogram verisi oluştur
    const numBars = 20;
    const bars = [];
    const values = [];
    const frequencies = [];
    
    for (let i = 0; i < numBars; i++) {
        const value = min + (max - min) * (i / (numBars - 1));
        // Normal dağılım benzeri yükseklik hesapla
        const distance = Math.abs(value - mean) / std;
        let height = Math.max(5, 100 * Math.exp(-0.5 * distance * distance));
        
        // NaN ve Infinity kontrolü
        if (!isFinite(height)) {
            height = 20;
        }
        
        bars.push(height);
        values.push(value.toFixed(1));
        frequencies.push(Math.floor(height * 10));
    }
    
    // Ek istatistikleri hesapla
    const range = (max - min).toFixed(2);
    const q1 = (min + (mean - min) * 0.5).toFixed(2);
    const q3 = (mean + (max - mean) * 0.5).toFixed(2);
    const mode = mean.toFixed(2);
    
    return {
        bars,
        values,
        frequencies,
        range,
        q1,
        q3,
        mode
    };
}

// Tab functionality
function showTab(evt, tabName) {
    var i, tabcontent, tablinks;
    
    // Hide all tab contents
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].classList.remove("active");
    }
    
    // Remove active class from all tab buttons
    tablinks = document.getElementsByClassName("tab-nav-item");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove("active");
    }
    
    // Show the selected tab and mark button as active
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
    
    // Çift analiz durumlarını temizle (tab değişiminde)
    cleanupDuplicateAnalysisStatus();
}

// File upload functionality
function setupFileInput() {
    document.getElementById('fileInput').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const fileInfo = document.getElementById('file-info');
            const fileDetails = document.getElementById('file-details');
            
            fileDetails.innerHTML = `
                <p><strong>Dosya Adı:</strong> ${file.name}</p>
                <p><strong>Boyut:</strong> ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
                <p><strong>Tip:</strong> ${file.type}</p>
            `;
            
            fileInfo.style.display = 'block';
        }
    });
}

function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const projectNameInput = document.getElementById('projectNameInput');
    
    if (!projectNameInput.value.trim()) {
        alert('Lütfen proje adını girin.');
        projectNameInput.focus();
        return;
    }
    
    if (fileInput.files[0]) {
        const file = fileInput.files[0];
        const projectName = projectNameInput.value.trim();
        
        // FormData oluştur
        const formData = new FormData();
        formData.append('file', file);
        
        // Upload URL'ini project name ile oluştur - Flask backend'e yönlendir
        const backendUrl = 'http://127.0.0.1:5000'; // Flask default port
        const uploadUrl = `${backendUrl}/upload/${encodeURIComponent(projectName)}`;
        
        // Loading göster
        const uploadBtn = document.querySelector('.tab-btn[onclick="uploadFile()"]');
        const originalText = uploadBtn.textContent;
        uploadBtn.textContent = 'Yükleniyor...';
        uploadBtn.disabled = true;
        
        // Fetch ile dosyayı yükle
        fetch(uploadUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                currentAnalysisProject = projectName;
                alert(`Dosya başarıyla yüklendi!\nProje: ${data.project_name}\nDosya: ${data.file_name}\n\nVeri analizi arkaplanda başlatıldı...`);
                
                // File info güncelle
                const fileDetails = document.getElementById('file-details');
                
                // Mevcut proje bilgilerini temizle
                const existingProjectInfo = fileDetails.querySelectorAll('p');
                existingProjectInfo.forEach(p => {
                    if (p.innerHTML.includes('Proje Adı:') || 
                        p.innerHTML.includes('Dosya Yolu:') || 
                        p.innerHTML.includes('Analiz Durumu:')) {
                        p.remove();
                    }
                });
                
                // Temel dosya bilgilerini koru ve proje bilgilerini ekle
                const file = document.getElementById('fileInput').files[0];
                if (file) {
                    const basicFileInfo = `
                        <p><strong>Dosya Adı:</strong> ${file.name}</p>
                        <p><strong>Boyut:</strong> ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
                        <p><strong>Tip:</strong> ${file.type}</p>
                    `;
                    
                    // Mevcut analiz durumunu kontrol et
                    const existingStatusElement = document.getElementById('analysis-status');
                    let currentStatus = 'Beklemede...';
                    let currentColor = 'blue';
                    
                    // Eğer önceki analiz durumu varsa, onu kontrol et
                    if (existingStatusElement) {
                        const currentText = existingStatusElement.textContent;
                        const currentStyle = existingStatusElement.style.color;
                        
                        if (currentText === 'Tamamlandı' && (currentStyle === 'green' || currentStyle.includes('rgb(0, 128, 0)'))) {
                            currentStatus = 'Tamamlandı';
                            currentColor = 'green';
                            console.log('Preserving completed analysis status');
                        } else if (currentText === 'Hata oluştu' && (currentStyle === 'red' || currentStyle.includes('rgb(255, 0, 0)'))) {
                            // Hata durumunda beklemede göster, analiz başlarsa güncellenir
                            currentStatus = 'Beklemede...';
                            currentColor = 'blue';
                        } else {
                            // Diğer durumlar için beklemede göster
                            currentStatus = 'Beklemede...';
                            currentColor = 'blue';
                        }
                    }
                    
                    const projectInfo = `
                        <p><strong>Proje Adı:</strong> ${data.project_name}</p>
                        <p><strong>Dosya Yolu:</strong> ${data.file_path}</p>
                        <p><strong>Analiz Durumu:</strong> <span style="color: ${currentColor};" id="analysis-status">${currentStatus}</span></p>
                    `;
                    
                    fileDetails.innerHTML = basicFileInfo + projectInfo;
                }
                
                // Sütun adlarını yükle
                loadColumnsAfterUpload(data.project_name, data.file_name);
                
            } else {
                alert('Hata: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            alert('Dosya yükleme sırasında hata oluştu.');
        })
        .finally(() => {
            // Button'u eski haline döndür
            uploadBtn.textContent = originalText;
            uploadBtn.disabled = false;
        });
        
    } else {
        alert('Lütfen önce bir dosya seçin.');
    }
}

function clearFile() {
    document.getElementById('fileInput').value = '';
    document.getElementById('projectNameInput').value = '';
    document.getElementById('file-info').style.display = 'none';
    
    // File details içeriğini temizle
    const fileDetails = document.getElementById('file-details');
    if (fileDetails) {
        fileDetails.innerHTML = '';
    }
    
    // Analiz projesini temizle
    currentAnalysisProject = null;
    
    // Analiz sonuçlarını temizle
    window.lastAnalysisResults = null;
    window.currentProjectColumns = null;
    window.currentProjectInfo = null;
    
    console.log('File and project data cleared');
}

// Operations functionality
function toggleOperation(element) {
    const checkbox = element.querySelector('.operation-checkbox');
    checkbox.classList.toggle('checked');
}

function applyOperations() {
    const checkedOperations = document.querySelectorAll('.operation-checkbox.checked');
    if (checkedOperations.length > 0) {
        alert(`${checkedOperations.length} işlem uygulanacak.`);
        // Implement operation logic here
    } else {
        alert('Lütfen en az bir işlem seçin.');
    }
}

function resetOperations() {
    const checkboxes = document.querySelectorAll('.operation-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.classList.remove('checked');
    });
    
    // Reset radio buttons to default
    const radioGroups = document.querySelectorAll('input[type="radio"]');
    radioGroups.forEach(radio => {
        radio.checked = false;
    });
    
    // Set first radio in each group as checked
    const firstRadio = document.querySelector('input[name="whitespace-type"]');
    if (firstRadio) {
        firstRadio.checked = true;
    }
    
    // Close all advanced operations
    const advancedOps = document.querySelectorAll('.advanced-operation');
    advancedOps.forEach(op => {
        op.classList.remove('expanded');
    });
    
    const details = document.querySelectorAll('.operation-details');
    details.forEach(detail => {
        detail.style.display = 'none';
    });
}

// Advanced operations functionality
function toggleAdvancedOperation(element, operationType) {
    // Toggle the main checkbox
    const checkbox = element.querySelector('.operation-checkbox');
    checkbox.classList.toggle('checked');
    
    // Toggle the expanded state
    element.classList.toggle('expanded');
    
    // Show/hide the details
    const detailsId = operationType + '-details';
    const details = document.getElementById(detailsId);
    
    if (details) {
        if (details.style.display === 'none' || !details.style.display) {
            details.style.display = 'block';
        } else {
            details.style.display = 'none';
        }
    }
}

// Visualization functionality
let selectedChart = null;

function selectVisualization(element, type) {
    // Remove selection from all options
    document.querySelectorAll('.viz-option').forEach(option => {
        option.classList.remove('selected');
    });
    
    // Mark selected option
    element.classList.add('selected');
    selectedChart = type;
    
    // Show chart configuration
    document.getElementById('chart-config').style.display = 'block';
}

function generateChart() {
    if (!selectedChart) {
        alert('Lütfen bir grafik türü seçin.');
        return;
    }
    
    const xAxis = document.getElementById('x-axis').value;
    const yAxis = document.getElementById('y-axis').value;
    const title = document.getElementById('chart-title').value;
    
    alert(`${selectedChart} grafiği oluşturuluyor...`);
    // Implement chart generation logic here
}

function downloadChart() {
    if (!selectedChart) {
        alert('Önce bir grafik oluşturun.');
        return;
    }
    alert('Grafik indiriliyor...');
}

function refreshData() {
    // Eğer analiz sonuçları mevcutsa onları göster
    if (window.lastAnalysisResults) {
        updateDataInfoFromAnalysis(window.lastAnalysisResults);
    } else {
        // Analiz sonucu yoksa bilgilendir
        const previewDiv = document.querySelector('#data-preview-table div');
        if (previewDiv) {
            previewDiv.innerHTML = 'Henüz veri analizi yapılmadı. Lütfen önce bir dosya yükleyin.';
            previewDiv.style.color = 'rgba(255,255,255,0.6)';
        }
    }
}

// Affected Values Preview Functions
function togglePreview() {
    const content = document.getElementById('affected-values-content');
    const icon = document.getElementById('preview-icon');
    const text = document.getElementById('preview-text');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'ri-eye-off-line';
        text.textContent = 'Önizlemeyi Gizle';
        updateAffectedValues();
    } else {
        content.style.display = 'none';
        icon.className = 'ri-eye-line';
        text.textContent = 'Önizlemeyi Göster';
    }
}

// Generic toggle preview function for any operation
function togglePreviewGeneric(operationType) {
    const content = document.getElementById(`${operationType}-values-content`);
    const icon = document.getElementById(`${operationType}-preview-icon`);
    const text = document.getElementById(`${operationType}-preview-text`);
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.className = 'ri-eye-off-line';
        text.textContent = 'Önizlemeyi Gizle';
        updateAffectedValuesGeneric(operationType);
    } else {
        content.style.display = 'none';
        icon.className = 'ri-eye-line';
        text.textContent = 'Önizlemeyi Göster';
    }
}

function updateAffectedValues() {
    const selectedType = document.querySelector('input[name="whitespace-type"]:checked').value;
    const affectedCount = document.getElementById('affected-count');
    const cleanedValues = document.getElementById('cleaned-values');
    
    // Check if we have project data to analyze
    if (currentAnalysisProject && window.lastAnalysisResults) {
        // Get selected columns for whitespace operation
        const selectedColumns = getSelectedColumns('whitespace-columns');
        const parameters = { type: selectedType };
        if (selectedColumns.length > 0) {
            parameters.columns = selectedColumns;
        }
        
        // Use real data for calculation
        calculateRealAffectedValues('RemoveWhitespace', parameters, affectedCount, cleanedValues);
    } else {
        // Fallback to sample data
        const originalData = ['" Örnek Veri "', '"  Test  "', '"Başlık   "', '"   Sonuç"', '"Çoklu    Boşluk"'];
        let cleanedData = [];
        let count = Math.floor(Math.random() * 150) + 50; // Random count between 50-200
        
        switch(selectedType) {
            case 'leading':
                cleanedData = ['"Örnek Veri "', '"Test  "', '"Başlık   "', '"Sonuç"', '"Çoklu    Boşluk"'];
                break;
            case 'trailing':
                cleanedData = ['" Örnek Veri"', '"  Test"', '"Başlık"', '"   Sonuç"', '"Çoklu    Boşluk"'];
                break;
            case 'multiple':
                cleanedData = ['" Örnek Veri "', '"  Test  "', '"Başlık   "', '"   Sonuç"', '"Çoklu Boşluk"'];
                break;
            case 'all':
                cleanedData = ['"ÖrnekVeri"', '"Test"', '"Başlık"', '"Sonuç"', '"ÇokluBoşluk"'];
                count = Math.floor(count * 1.5); // More values affected when removing all spaces
                break;
        }
        
        // Update count
        affectedCount.textContent = count;
        
        // Update cleaned values display
        cleanedValues.innerHTML = cleanedData.map(value => 
            `<span class="value-item">${value}</span>`
        ).join('');
    }
}

// Generic update function for any operation type
function updateAffectedValuesGeneric(operationType) {
    const affectedCount = document.getElementById(`${operationType}-affected-count`);
    const cleanedValues = document.getElementById(`${operationType}-cleaned-values`);
    
    // Check if we have project data to analyze
    if (currentAnalysisProject && window.lastAnalysisResults) {
        // Use real data for calculation
        calculateRealAffectedValuesGeneric(operationType, affectedCount, cleanedValues);
    } else {
        // Fallback to sample data
        let count = Math.floor(Math.random() * 200) + 30;
        let cleanedData = [];
        
        switch(operationType) {
            case 'duplicate':
                cleanedData = ['"Benzersiz Veri 1"', '"Benzersiz Veri 2"', '"Tekil Kayıt"'];
                count = Math.floor(Math.random() * 50) + 10;
                break;
            case 'special-chars':
                cleanedData = ['"Temiz Metin"', '"Normal Veri"', '"Duzgun Baslik"'];
                break;
            case 'case-normalize':
                cleanedData = ['"örnek başlık"', '"test verisi"', '"standart format"'];
                break;
            case 'delete-columns':
                const selectedColumns = document.getElementById('delete-columns-columns');
                const selected = selectedColumns ? Array.from(selectedColumns.selectedOptions).length : 2;
                cleanedData = ['📊 ID', '📄 İsim', '📄 Soyisim', '📊 Yaş'];
                count = selected;
                break;
            case 'data-types':
                cleanedData = ['123 (int)', '45.67 (float)', '"2024-01-15" (date)', 'true (bool)'];
                break;
            case 'categorical':
                cleanedData = ['1', '2', '3', '4'];
                break;
            case 'date-format':
                cleanedData = ['"2024-01-15"', '"2024-02-20"', '"2024-03-10"'];
                break;
            case 'normalization':
                updateNormalizationPreview();
                return; // Return early since we have a custom function
        }
        
        if (affectedCount) affectedCount.textContent = count;
        if (cleanedValues) {
            cleanedValues.innerHTML = cleanedData.map(value => 
                `<span class="value-item">${value}</span>`
            ).join('');
        }
    }
}

// Real data calculation function for whitespace operations
function calculateRealAffectedValues(operationType, parameters, affectedCountElement, cleanedValuesElement) {
    if (!currentAnalysisProject) return;
    
    // Get current project and file name
    const projectName = currentAnalysisProject;
    const fileName = document.getElementById('fileInput').files[0]?.name || 'data.csv';
    
    // Prepare data for suitability check
    const processData = [{
        name: operationType,
        params: parameters
    }];
    
    // Show loading state
    if (affectedCountElement) {
        affectedCountElement.innerHTML = '<i class="ri-loader-line"></i> Hesaplanıyor...';
        affectedCountElement.style.color = '#ffd43b';
        // Store reference to update later
        affectedCountElement.setAttribute('data-calculating', 'true');
    }
    
    // Send WebSocket request for suitability calculation
    socket.emit('calculate_suitability', {
        project_name: projectName,
        file_name: fileName,
        processes: processData
    });
}

// Real data calculation function for generic operations
function calculateRealAffectedValuesGeneric(operationType, affectedCountElement, cleanedValuesElement) {
    if (!currentAnalysisProject) return;
    
    // Get operation parameters based on type
    let parameters = {};
    
    switch(operationType) {
        case 'duplicate':
            const duplicateType = document.querySelector('input[name="duplicate-type"]:checked')?.value || 'all';
            const duplicateColumns = getSelectedColumns(`${operationType}-columns`);
            parameters = { type: duplicateType };
            if (duplicateColumns.length > 0) parameters.columns = duplicateColumns;
            break;
        case 'special-chars':
            const specialCharsType = document.querySelector('input[name="special-chars-type"]:checked')?.value || 'all';
            const specialCharsColumns = getSelectedColumns(`${operationType}-columns`);
            parameters = { type: specialCharsType };
            if (specialCharsColumns.length > 0) parameters.columns = specialCharsColumns;
            break;
        case 'case-normalize':
            const caseType = document.querySelector('input[name="case-normalize-type"]:checked')?.value || 'lower';
            const caseColumns = getSelectedColumns(`${operationType}-columns`);
            parameters = { type: caseType };
            if (caseColumns.length > 0) parameters.columns = caseColumns;
            break;
        // Add more cases as needed
    }
    
    // Map frontend operation names to backend operation names
    const operationMap = {
        'duplicate': 'DeleteDupValues',
        'special-chars': 'StripSpecialChars',
        'case-normalize': 'LowercaseColumns',
        'delete-columns': 'DropColumn',
        'data-types': 'AutoFixNumericColumns',
        'categorical': 'categoricalToNumeric',
        'date-format': 'dateFormat',
        'normalization': 'scaleValues'
    };
    
    const backendOperationType = operationMap[operationType] || operationType;
    
    calculateRealAffectedValues(backendOperationType, parameters, affectedCountElement, cleanedValuesElement);
}

// Helper function to get selected columns from a dropdown
function getSelectedColumns(selectId) {
    const selectElement = document.getElementById(selectId);
    if (!selectElement) return [];
    
    const selectedOptions = Array.from(selectElement.selectedOptions);
    const selectedValues = selectedOptions.map(option => option.value);
    
    // If "all" is selected, return null to indicate all columns
    if (selectedValues.includes('all')) {
        return [];
    }
    
    return selectedValues;
}

// Special function for normalization preview update
function updateNormalizationPreview() {
    const selectedType = document.querySelector('input[name="normalization-type"]:checked');
    const affectedCount = document.getElementById('normalization-affected-count');
    const cleanedValues = document.getElementById('normalization-cleaned-values');
    
    if (!selectedType || !affectedCount || !cleanedValues) return;
    
    const type = selectedType.value;
    
    // Check if we have project data to analyze
    if (currentAnalysisProject && window.lastAnalysisResults) {
        // Use real data for calculation
        let parameters = { type: type };
        
        if (type === 'custom') {
            parameters.min_val = parseFloat(document.getElementById('normalization-min')?.value || 0);
            parameters.max_val = parseFloat(document.getElementById('normalization-max')?.value || 1);
        }
        
        calculateRealAffectedValues('scaleValues', parameters, affectedCount, cleanedValues);
    } else {
        // Fallback to sample data
        let cleanedData = [];
        let count = Math.floor(Math.random() * 150) + 50;
        
        // Sample original data for demonstration
        const originalData = [1000, 2500, 750, 3200, 1800];
        
        switch(type) {
            case 'minmax':
                cleanedData = ['0.102', '0.714', '0.000', '1.000', '0.429'];
                break;
            case 'custom':
                const minVal = parseFloat(document.getElementById('normalization-min')?.value || 0);
                const maxVal = parseFloat(document.getElementById('normalization-max')?.value || 100);
                
                // Calculate custom range normalization
                const min = Math.min(...originalData);
                const max = Math.max(...originalData);
                const range = max - min;
                const targetRange = maxVal - minVal;
                
                cleanedData = originalData.map(val => {
                    const normalized = ((val - min) / range) * targetRange + minVal;
                    return normalized.toFixed(1);
                });
                break;
            case 'zscore':
                cleanedData = ['-0.845', '0.234', '-1.234', '1.567', '-0.123'];
                break;
            case 'robust':
                cleanedData = ['-0.567', '0.345', '-0.890', '0.890', '-0.234'];
                break;
            case 'unit':
                cleanedData = ['0.234', '0.567', '0.171', '0.729', '0.410'];
                break;
        }
        
        affectedCount.textContent = count;
        cleanedValues.innerHTML = cleanedData.map(value => 
            `<span class="value-item">${value}</span>`
        ).join('');
    }
}

// Template generator for advanced operations
function createAdvancedOperationTemplate(operationType, title, columns, options, originalExamples, cleanedExamples) {
    return `
        <li class="operation-details" id="${operationType}-details" style="display: none;">
            <div class="operation-config">
                <div class="config-row">
                    <label class="config-label">Sütun Seçimi (Çoklu Seçim):</label>
                    <div class="column-selector">
                        <select class="column-dropdown" id="${operationType}-columns" multiple size="5">
                            ${columns.map(col => `<option value="${col.value}">${col.text}</option>`).join('')}
                        </select>
                        <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.6); margin-top: 0.5rem; line-height: 1.3;">
                            💡 <strong>İpucu:</strong> Ctrl tuşuna basılı tutarak birden fazla sütun seçebilirsiniz
                        </div>
                    </div>
                </div>
                ${options ? `
                <div class="config-row">
                    <label class="config-label">${title} Seçenekleri:</label>
                    <div class="checkbox-group">
                        ${options.map(option => `
                            <label class="checkbox-item">
                                <input type="radio" name="${operationType}-type" value="${option.value}" ${option.checked ? 'checked' : ''}> ${option.text}
                            </label>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <!-- Etkilenen Değerler Bölümü -->
                <div class="config-row">
                    <label class="config-label">🎯 Etkilenen Değerler Önizlemesi:</label>
                    <div class="affected-values-container">
                        <div class="affected-values-header">
                            <div class="affected-count">
                                <i class="ri-information-line"></i>
                                <span id="${operationType}-affected-count">0</span> değer etkilenecek
                            </div>
                            <div class="toggle-preview" onclick="togglePreviewGeneric('${operationType}')">
                                <i class="ri-eye-line" id="${operationType}-preview-icon"></i>
                                <span id="${operationType}-preview-text">Önizlemeyi Göster</span>
                            </div>
                        </div>
                        
                        <div class="affected-values-content" id="${operationType}-values-content" style="display: none;">
                            <div class="values-section">
                                <h4 class="values-title">Örnek Mevcut Değerler:</h4>
                                <div class="values-list" id="${operationType}-original-values">
                                    ${originalExamples.map(value => `<span class="value-item">${value}</span>`).join('')}
                                </div>
                            </div>
                            
                            <div class="arrow-section">
                                <i class="ri-arrow-down-line transform-arrow"></i>
                            </div>
                            
                            <div class="values-section">
                                <h4 class="values-title">${title} Sonucu:</h4>
                                <div class="values-list" id="${operationType}-cleaned-values">
                                    ${cleanedExamples.map(value => `<span class="value-item">${value}</span>`).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </li>
    `;
}

// Dosya detaylarında analiz durumunu güncelle
function updateAnalysisStatusInFileDetails(status, color) {
    const fileDetails = document.getElementById('file-details');
    if (fileDetails) {
        // Önce spesifik ID'li elementi kontrol et
        const specificStatusElement = document.getElementById('analysis-status');
        if (specificStatusElement) {
            specificStatusElement.textContent = status;
            specificStatusElement.style.color = color;
            console.log('Updated specific analysis-status element:', status);
            return; // Spesifik element bulundu ve güncellendi
        }
        
        // Önce "Analiz Durumu:" içeren paragrafı bul
        const analysisParagraphs = Array.from(fileDetails.querySelectorAll('p')).filter(p => 
            p.innerHTML.includes('Analiz Durumu:')
        );
        
        if (analysisParagraphs.length > 0) {
            // Eğer birden fazla varsa, hepsini temizle ve sadece birini tut
            if (analysisParagraphs.length > 1) {
                console.log('Found multiple analysis status paragraphs, cleaning up...');
                // İlk paragrafı tut, diğerlerini sil
                for (let i = 1; i < analysisParagraphs.length; i++) {
                    analysisParagraphs[i].remove();
                }
            }
            
            // Kalan paragrafı güncelle
            const targetParagraph = analysisParagraphs[0];
            targetParagraph.innerHTML = `<strong>Analiz Durumu:</strong> <span style="color: ${color};" id="analysis-status">${status}</span>`;
            
        } else {
            // Eğer hiç analiz durumu paragrafı yoksa, yeni bir tane ekle
            const analysisStatusP = document.createElement('p');
            analysisStatusP.innerHTML = `<strong>Analiz Durumu:</strong> <span style="color: ${color};" id="analysis-status">${status}</span>`;
            fileDetails.appendChild(analysisStatusP);
        }
    }
}

// Analiz durumunu progress ile güncelle
function updateAnalysisStatusWithProgress(message, progress = null) {
    // Önce spesifik ID'li elementi kontrol et
    const specificStatusElement = document.getElementById('analysis-status');
    if (specificStatusElement) {
        if (progress !== null) {
            specificStatusElement.textContent = `${message} (${progress}%)`;
        } else {
            specificStatusElement.textContent = message;
        }
        specificStatusElement.style.color = 'orange';
        console.log('Updated specific analysis-status with progress:', message);
        return;
    }
    
    // Fallback: file-details içinde ara
    const fileDetails = document.getElementById('file-details');
    if (fileDetails) {
        const statusSpan = fileDetails.querySelector('span[style*="color: orange"]') || 
                          fileDetails.querySelector('span[style*="color: green"]') || 
                          fileDetails.querySelector('span[style*="color: red"]');
        
        if (statusSpan) {
            if (progress !== null) {
                statusSpan.textContent = `${message} (${progress}%)`;
            } else {
                statusSpan.textContent = message;
            }
            statusSpan.style.color = 'orange';
        }
    }
}

// Çift analiz durumlarını temizle
function cleanupDuplicateAnalysisStatus() {
    const fileDetails = document.getElementById('file-details');
    if (fileDetails) {
        // Çoklu analysis-status ID'li elementleri kontrol et
        const duplicateStatusElements = document.querySelectorAll('#analysis-status');
        if (duplicateStatusElements.length > 1) {
            console.log(`Found ${duplicateStatusElements.length} duplicate analysis-status elements, cleaning up...`);
            // İlkini tut, diğerlerini sil
            for (let i = 1; i < duplicateStatusElements.length; i++) {
                duplicateStatusElements[i].parentElement.remove(); // Tüm paragrafı sil
            }
        }
        
        const analysisParagraphs = Array.from(fileDetails.querySelectorAll('p')).filter(p => 
            p.innerHTML.includes('Analiz Durumu:')
        );
        
        if (analysisParagraphs.length > 1) {
            console.log(`Found ${analysisParagraphs.length} duplicate analysis status paragraphs, cleaning up...`);
            // İlk paragrafı tut, diğerlerini sil
            for (let i = 1; i < analysisParagraphs.length; i++) {
                analysisParagraphs[i].remove();
            }
            console.log('Cleanup complete');
        }
    }
}

// Mevcut çift durumları temizle
function fixCurrentDuplicates() {
    cleanupDuplicateAnalysisStatus();
    alert('Çift analiz durumları temizlendi!');
}

// Global olarak erişilebilir yap
window.cleanupDuplicateAnalysisStatus = cleanupDuplicateAnalysisStatus;
window.fixCurrentDuplicates = fixCurrentDuplicates;

// ...existing code...

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Setup file input
    setupFileInput();
    
    // Başlangıç durumunda veri bilgisi kartlarını sıfırla
    const dataElements = [
        'total-rows', 'total-columns', 'file-size', 'missing-values', 
        'numeric-columns', 'categorical-columns', 'avg-skewness', 
        'avg-std', 'avg-variance', 'correlation-status'
    ];
    
    dataElements.forEach(elementId => {
        const element = document.getElementById(elementId);
        if (element) {
            if (elementId === 'correlation-status') {
                element.textContent = 'Bekleniyor';
            } else {
                element.textContent = '-';
            }
        }
    });
    
    // Sütun istatistikleri alanını temizle
    const columnStatsDiv = document.getElementById('column-statistics');
    if (columnStatsDiv) {
        columnStatsDiv.innerHTML = `
            <div style="text-align: center; color: rgba(255,255,255,0.6); padding: 2rem;">
                Veri analizi tamamlandıktan sonra detaylı sütun istatistikleri burada görüntülenecek.
            </div>
        `;
    }
    
    // Veri önizleme alanını temizle
    const previewDiv = document.querySelector('#data-preview-table div');
    if (previewDiv) {
        previewDiv.innerHTML = 'Henüz veri yüklenmedi. Dosya yükledikten sonra veri önizlemesi burada görüntülenecek.';
        previewDiv.style.color = 'rgba(255,255,255,0.6)';
    }
    
    // Add column selection functionality
    const columnDropdown = document.getElementById('whitespace-columns');
    if (columnDropdown) {
        columnDropdown.addEventListener('change', function(e) {
            const selectedOptions = Array.from(this.selectedOptions);
            const allOption = this.querySelector('option[value="all"]');
            
            // If "Tüm Sütunlar" is selected
            if (selectedOptions.includes(allOption)) {
                // If other options were also selected, only keep "Tüm Sütunlar"
                if (selectedOptions.length > 1) {
                    // Clear all selections
                    for (let option of this.options) {
                        option.selected = false;
                    }
                    // Select only "Tüm Sütunlar"
                    allOption.selected = true;
                }
            } else {
                // If individual columns are selected, make sure "Tüm Sütunlar" is not selected
                allOption.selected = false;
            }
        });
    }
    
    // Add radio button change listeners for whitespace type
    const radioButtons = document.querySelectorAll('input[name="whitespace-type"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            if (document.getElementById('affected-values-content').style.display === 'block') {
                updateAffectedValues();
            }
        });
    });
    
    // Add radio button change listeners for all operation types
    const allRadioGroups = [
        'duplicate-type', 'special-chars-type', 'case-normalize-type', 
        'delete-columns-type', 'data-types-type', 'categorical-type', 'date-format-type', 
        'normalization-type', 'outliers-type', 'conditional-type', 'sampling-type'
    ];
    
    allRadioGroups.forEach(groupName => {
        const radios = document.querySelectorAll(`input[name="${groupName}"]`);
        radios.forEach(radio => {
            radio.addEventListener('change', function() {
                const operationType = groupName.replace('-type', '');
                
                // Special handling for normalization custom range
                if (operationType === 'normalization') {
                    const customRangeSettings = document.getElementById('custom-range-settings');
                    if (customRangeSettings) {
                        if (this.value === 'custom') {
                            customRangeSettings.style.display = 'block';
                        } else {
                            customRangeSettings.style.display = 'none';
                        }
                    }
                }
                
                const contentId = `${operationType}-values-content`;
                if (document.getElementById(contentId) && document.getElementById(contentId).style.display === 'block') {
                    updateAffectedValuesGeneric(operationType);
                }
            });
        });
    });
    
    // Add listeners for normalization custom range inputs
    const normalizationMinInput = document.getElementById('normalization-min');
    const normalizationMaxInput = document.getElementById('normalization-max');
    
    [normalizationMinInput, normalizationMaxInput].forEach(input => {
        if (input) {
            input.addEventListener('input', function() {
                const customRadio = document.querySelector('input[name="normalization-type"][value="custom"]');
                if (customRadio && customRadio.checked) {
                    const contentId = 'normalization-values-content';
                    if (document.getElementById(contentId) && document.getElementById(contentId).style.display === 'block') {
                        updateNormalizationPreview();
                    }
                }
            });
        }
    });
    
    // Add column dropdown listeners for all operations
    const allColumnDropdowns = [
        'duplicate-columns', 'special-chars-columns', 'case-normalize-columns',
        'delete-columns-columns', 'data-types-columns', 'categorical-columns', 'date-format-columns',
        'normalization-columns', 'outliers-columns', 'range-filter-columns'
    ];
    
    allColumnDropdowns.forEach(dropdownId => {
        const dropdown = document.getElementById(dropdownId);
        if (dropdown) {
            dropdown.addEventListener('change', function(e) {
                const selectedOptions = Array.from(this.selectedOptions);
                const allOption = this.querySelector('option[value="all"]');
                
                // If "Tüm Sütunlar" is selected
                if (allOption && selectedOptions.includes(allOption)) {
                    // If other options were also selected, only keep "Tüm Sütunlar"
                    if (selectedOptions.length > 1) {
                        // Clear all selections
                        for (let option of this.options) {
                            option.selected = false;
                        }
                        // Select only "Tüm Sütunlar"
                        allOption.selected = true;
                    }
                } else {
                    // If individual columns are selected, make sure "Tüm Sütunlar" is not selected
                    allOption.selected = false;
                }
            });
        }
    });
    
    // Mevcut proje için sütun adlarını yükle
    function loadCurrentProjectColumns() {
        if (currentAnalysisProject && window.lastAnalysisResults) {
            // Eğer currentAnalysisProject varsa, dosya adını bul
            const fileInput = document.getElementById('fileInput');
            const fileName = fileInput.files[0]?.name || 'data.csv';
            
            console.log('Loading columns for current project:', currentAnalysisProject, fileName);
            requestColumnNames(currentAnalysisProject, fileName);
        } else {
            console.log('No current project found, using default columns');
            // Varsayılan sütun adlarını göster
            populateColumnDropdowns([
                { name: 'Column1', type: 'object', is_numeric: false, is_string: true, null_count: 0, unique_count: 100 },
                { name: 'Column2', type: 'int64', is_numeric: true, is_string: false, null_count: 5, unique_count: 50 },
                { name: 'Column3', type: 'float64', is_numeric: true, is_string: false, null_count: 2, unique_count: 80 }
            ]);
        }
    }

    // Sayfa yüklendiğinde sütun adlarını yükle
    function initializeColumnDropdowns() {
        // Sayfa yüklendiğinde mevcut proje varsa sütunları yükle
        setTimeout(() => {
            loadCurrentProjectColumns();
        }, 500);
    }

    
    // İlk yüklemede sütun adlarını yükle
    initializeColumnDropdowns();
});
