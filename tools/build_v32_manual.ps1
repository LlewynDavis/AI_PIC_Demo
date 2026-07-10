param(
    [string]$OutputPath = "D:\AI_PIC_Demo\AI光子芯片设计平台Demo介绍与说明书_V3.2_最新版.docx"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$run = Join-Path $root "outputs\run_20260706_011215"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

function End-Range($doc) {
    return $doc.Range($doc.Content.End - 1, $doc.Content.End - 1)
}

function Add-Para($doc, [string]$text, [string]$style = "正文", [int]$spaceAfter = 6) {
    $r = End-Range $doc
    $r.Text = $text + "`r"
    try { $r.Style = $style } catch { $r.Style = "正文" }
    $r.ParagraphFormat.SpaceAfter = $spaceAfter
    return $r.Paragraphs.Item(1)
}

function Add-Bullets($doc, [string[]]$items) {
    foreach ($item in $items) {
        $p = Add-Para $doc $item "正文" 3
        $p.Range.ListFormat.ApplyBulletDefault()
        $p.Range.ParagraphFormat.LeftIndent = 21
        $p.Range.ParagraphFormat.FirstLineIndent = -10.5
    }
}

function Add-Numbered($doc, [string[]]$items) {
    foreach ($item in $items) {
        $p = Add-Para $doc $item "正文" 3
        $p.Range.ListFormat.ApplyNumberDefault()
        $p.Range.ParagraphFormat.LeftIndent = 21
        $p.Range.ParagraphFormat.FirstLineIndent = -10.5
    }
}

function Add-Callout($doc, [string]$text) {
    $t = Add-Table $doc @(@("核心结论", $text), @("", "")) @(85, 360) $false
    $t.Rows.Item(2).Delete()
    $t.Cell(1,1).Shading.BackgroundPatternColor = 15263976
    $t.Cell(1,2).Shading.BackgroundPatternColor = 16119285
    $t.Cell(1,1).Range.Font.Bold = 1
    return $t
}

function Add-Table($doc, [object[]]$data, [int[]]$widths, [bool]$header = $true) {
    $rows = $data.Count
    $cols = $data[0].Count
    $r = End-Range $doc
    $table = $doc.Tables.Add($r, $rows, $cols)
    $table.AllowAutoFit = $false
    $table.Borders.Enable = 1
    $table.Range.Font.NameFarEast = "等线"
    $table.Range.Font.Name = "Arial"
    $table.Range.Font.Size = 9.5
    $table.Range.ParagraphFormat.SpaceAfter = 0
    $table.Range.ParagraphFormat.SpaceBefore = 0
    for ($i=1; $i -le $rows; $i++) {
        $table.Rows.Item($i).AllowBreakAcrossPages = 0
        for ($j=1; $j -le $cols; $j++) {
            $table.Cell($i,$j).Range.Text = [string]$data[$i-1][$j-1]
            if ($j -le $widths.Count) { $table.Cell($i,$j).Width = $widths[$j-1] }
            $table.Cell($i,$j).VerticalAlignment = 1
        }
    }
    if ($header) {
        $table.Rows.Item(1).HeadingFormat = -1
        $table.Rows.Item(1).Range.Font.Bold = 1
        $table.Rows.Item(1).Range.Font.Color = 16777215
        $table.Rows.Item(1).Shading.BackgroundPatternColor = 7556864
    }
    $after = End-Range $doc
    $after.InsertParagraphAfter()
    return $table
}

function Add-Picture($doc, [string]$path, [string]$caption, [double]$maxWidth = 430) {
    if (-not (Test-Path $path)) { return }
    $r = End-Range $doc
    $pic = $doc.InlineShapes.AddPicture($path, $false, $true, $r)
    $pic.LockAspectRatio = -1
    if ($pic.Width -gt $maxWidth) { $pic.Width = $maxWidth }
    $pic.Range.ParagraphFormat.Alignment = 1
    (End-Range $doc).InsertParagraphAfter()
    $p = Add-Para $doc $caption "题注" 8
    $p.Range.ParagraphFormat.Alignment = 1
}

function Add-PageBreak($doc) {
    $r = End-Range $doc
    $r.InsertBreak(7)
}

try {
    $doc = $word.Documents.Add()
    $doc.PageSetup.TopMargin = 56.7
    $doc.PageSetup.BottomMargin = 56.7
    $doc.PageSetup.LeftMargin = 65.2
    $doc.PageSetup.RightMargin = 65.2
    $doc.PageSetup.DifferentFirstPageHeaderFooter = -1

    $normal = $doc.Styles.Item("正文")
    $normal.Font.NameFarEast = "等线"
    $normal.Font.Name = "Arial"
    $normal.Font.Size = 10.5
    $normal.ParagraphFormat.LineSpacingRule = 1
    $normal.ParagraphFormat.LineSpacing = 18
    $normal.ParagraphFormat.FirstLineIndent = 21
    $normal.ParagraphFormat.Alignment = 0

    foreach ($name in @("标题 1","标题 2","标题 3")) {
        $s = $doc.Styles.Item($name)
        $s.Font.NameFarEast = "微软雅黑"
        $s.Font.Name = "Arial"
        $s.Font.Color = 7556864
        $s.Font.Bold = 1
    }
    $doc.Styles.Item("标题 1").Font.Size = 17
    $doc.Styles.Item("标题 2").Font.Size = 13
    $doc.Styles.Item("标题 3").Font.Size = 11
    $doc.Styles.Item("题注").Font.NameFarEast = "等线"
    $doc.Styles.Item("题注").Font.Size = 9
    $doc.Styles.Item("题注").Font.Color = 8421504

    # 封面
    $p = Add-Para $doc "AI 光子芯片设计平台 Demo" "标题" 10
    $p.Range.Font.NameFarEast = "微软雅黑"
    $p.Range.Font.Size = 30
    $p.Range.Font.Bold = 1
    $p.Range.Font.Color = 7556864
    $p.Range.ParagraphFormat.Alignment = 1
    $p.Range.ParagraphFormat.SpaceBefore = 120
    $p = Add-Para $doc "项目介绍与使用说明书" "副标题" 24
    $p.Range.Font.NameFarEast = "微软雅黑"
    $p.Range.Font.Size = 21
    $p.Range.Font.Color = 9351321
    $p.Range.ParagraphFormat.Alignment = 1
    Add-Picture $doc (Join-Path $run "field_propagation_enhanced.png") "" 390
    $p = Add-Para $doc "以 SOI 平台 1×2 MMI 光功率分束器为演示对象" "正文" 4
    $p.Range.Font.Size = 12
    $p.Range.Font.Bold = 1
    $p.Range.ParagraphFormat.Alignment = 1
    $p.Range.ParagraphFormat.FirstLineIndent = 0
    $p = Add-Para $doc "当前版本：V3.2_port_mode_overlap" "正文" 4
    $p.Range.ParagraphFormat.Alignment = 1; $p.Range.ParagraphFormat.FirstLineIndent = 0
    $p = Add-Para $doc "汇报对象：程教授　｜　更新日期：2026 年 7 月 6 日" "正文" 4
    $p.Range.ParagraphFormat.Alignment = 1; $p.Range.ParagraphFormat.FirstLineIndent = 0
    Add-PageBreak $doc

    # 目录
    Add-Para $doc "目录" "标题 1" 12 | Out-Null
    $tocRange = End-Range $doc
    $toc = $doc.TablesOfContents.Add($tocRange, $true, 1, 3)
    Add-PageBreak $doc

    Add-Para $doc "文档摘要" "标题 1" 8 | Out-Null
    Add-Callout $doc "当前平台已从旧版 V0.7 的流程演示，升级为包含二维标量有限差分模式求解、MMI 宽度—长度优化、二维标量 BPM 传播验证、窗口敏感性校准、端口模式重叠功率提取、GDS 生成、网页展示、中文报告与结果打包的 V3.2 原型。"
    Add-Para $doc "本说明书面向项目汇报和现场演示，统一说明当前实现、算法链路、最新一次完整运行结果、启动与操作方法、输出文件、模型边界及后续研究路线。文中数值均来自 2026 年 7 月 6 日 01:12 完成的本地运行目录 outputs/run_20260706_011215。" "正文" 6 | Out-Null
    Add-Table $doc @(
        @("判断维度","当前结论","证据"),
        @("流程完整性","已形成从设计意图到版图和报告的自动闭环","命令行与 Streamlit 均可运行；单次运行独立归档"),
        @("物理可信度","已引入标量模式场和 BPM 传播，强于纯经验模型","mode_result.json、field_propagation_enhanced.png"),
        @("功率提取","V3.2 新增端口模式重叠，降低窗口积分口径歧义","mode_overlap_result.json、mode_overlap_comparison.png"),
        @("工程成熟度","适合教学、原型验证与研究流程展示","尚不能直接作为流片签核依据")
    ) @(90,220,140) $true | Out-Null

    Add-Para $doc "一、项目定位与本次版本更新" "标题 1" 8 | Out-Null
    Add-Para $doc "1.1 项目定位" "标题 2" 5 | Out-Null
    Add-Para $doc "AI_PIC_Demo 是一个面向光子芯片自动化设计研究的可运行原型。当前选取 SOI 平台 1×2 MMI 分束器作为最小案例，将自然语言设计意图、结构化参数、物理建模、参数优化、传播验证、版图生成和结果交付串联成统一流程。其研究价值不在于替代成熟商业 EDA，而在于建立可插拔的自动化骨架，使后续模式求解器、全波仿真器、PDK/DRC 和 AI Agent 能按模块接入。" "正文" 6 | Out-Null
    Add-Para $doc "1.2 从旧说明书到 V3.2 的实质升级" "标题 2" 5 | Out-Null
    Add-Table $doc @(
        @("阶段","核心能力","相对旧版的变化"),
        @("旧版 V0.7","规则解析、简化模型、长度扫描、GDS、网页与报告","验证了流程闭环"),
        @("V2.5","二维标量有限差分 Helmholtz 本征值求解","获得模式场、neff、约束因子和模式面积"),
        @("V3.0","二维标量 split-step Fourier BPM","获得 MMI 内部光场传播与输出场"),
        @("V3.1","输出窗口敏感性、增强传播图、Surrogate/BPM 对比","解释窗口积分的依赖性与两类模型的物理层级"),
        @("V3.2","Gaussian 端口模式与 BPM 复数场重叠积分","获得更具模式含义的端口功率和等效插损")
    ) @(70,175,205) $true | Out-Null

    Add-Para $doc "二、平台总体架构与自动化流程" "标题 1" 8 | Out-Null
    Add-Para $doc "平台采用分层、可替换的模块架构。前端负责表达和确认设计意图，中间层负责求解、优化与校准，后端负责版图和结果交付。各步骤通过 JSON、NPZ、PNG、GDS 和 Markdown 文件传递结果，便于复现、审计和后续替换算法。" "正文" 6 | Out-Null
    Add-Table $doc @(
        @("层级","输入/处理","主要模块","输出"),
        @("设计意图层","自然语言需求与参数确认","spec_parser / DesignSpec","design_spec.json"),
        @("模式与材料层","SOI 折射率截面、标量本征值求解","materials、mode_solver","mode_result.json、模式图"),
        @("优化层","MMI 宽度—长度扫描、波长扫描","mmi_model、optimizer、wavelength_sweep","optimization_result.json、热力图"),
        @("传播与校准层","二维标量 BPM、窗口敏感性、模型比较、模式重叠","propagation_solver、mode_overlap","传播图、校准 JSON/PNG"),
        @("版图与交付层","GDS、预览、中文报告、ZIP","gds_generator、report_generator、package_generator","GDS、report.md、结果包"),
        @("交互层","Streamlit 运行、结果预览与下载","app.py、v2_web_utils.py","可交互网页")
    ) @(70,135,150,100) $true | Out-Null
    Add-Para $doc "端到端执行顺序" "标题 2" 5 | Out-Null
    Add-Numbered $doc @(
        "输入并解析设计需求，生成结构化 DesignSpec。",
        "调用 SOI 材料参数，生成折射率截面并求解基模。",
        "将模式求解得到的 neff 传入 MMI 宽度—长度优化和波长扫描。",
        "对优化结构执行二维标量 BPM，保存完整传播场与末端复数场。",
        "执行窗口敏感性、Surrogate/BPM 趋势对比和 V3.2 端口模式重叠。",
        "生成 GDS、版图预览、中文报告、运行日志和完整 ZIP 结果包。"
    )

    Add-Para $doc "三、当前已完成功能" "标题 1" 8 | Out-Null
    Add-Table $doc @(
        @("功能域","已实现内容","主要输出"),
        @("输入与校验","自然语言规则解析、参数框确认、合法性检查","design_spec.json"),
        @("材料与模式","SOI 参数、二维标量有限差分模式、宽度扫描","index_profile.png、mode_profile.png、neff_vs_width.png"),
        @("器件优化","MMI 宽度—长度二维优化、长度曲线、波长趋势","optimization_result.json、width_length_heatmap.png、wavelength_sweep.png"),
        @("传播验证","二维标量 BPM、输出场、增强传播图","propagation_result.json、field_propagation*.png"),
        @("校准分析","窗口宽度敏感性、Surrogate/BPM 对比","output_window_sensitivity*.png/json、model_comparison*.png/json"),
        @("端口分析","Gaussian 端口模式、复数场重叠积分、三口径比较","mode_overlap_result.json、mode_overlap_comparison.png"),
        @("版图与交付","GDS、预览、报告、日志、完整性检查、ZIP","mmi1x2_demo.gds、layout_preview.png、report.md、run_log.txt"),
        @("交互与版本","Streamlit 展示下载、独立运行目录、版本文档","app.py、VERSION、CHANGELOG.md")
    ) @(80,240,135) $true | Out-Null

    Add-Para $doc "四、最新一次完整运行结果" "标题 1" 8 | Out-Null
    Add-Para $doc "4.1 运行基线" "标题 2" 5 | Out-Null
    Add-Table $doc @(
        @("项目","数值/说明"),
        @("运行目录","outputs/run_20260706_011215"),
        @("工作波长","1.55 μm"),
        @("波导截面","宽 0.50 μm，高 0.22 μm"),
        @("材料折射率","Si 3.48；包层 1.44"),
        @("模式网格","96 × 72；dx≈0.0421 μm，dy≈0.0423 μm"),
        @("BPM 网格","nx=512，nz=321；横向跨度 6 μm")
    ) @(150,310) $true | Out-Null
    Add-Para $doc "4.2 关键结果" "标题 2" 5 | Out-Null
    Add-Table $doc @(
        @("指标","结果","解释口径"),
        @("标量模式 neff","2.7415","有限差分标量 Helmholtz 基模"),
        @("约束因子","0.8251","当前离散模型下的场约束估计"),
        @("模式面积","0.1464 μm²","标量模式强度口径"),
        @("优化 MMI 宽度","2.449 μm","二维参数扫描最优点"),
        @("优化 MMI 长度","5.307 μm","二维参数扫描最优点"),
        @("Surrogate 分光","P1=0.5001，P2=0.4999","快速优化模型"),
        @("BPM 窗口积分总功率","0.4098","输出窗口宽 0.35 μm"),
        @("V3.2 模式重叠总功率","0.8434","简化 Gaussian 端口模式投影"),
        @("V3.2 等效插损","0.740 dB","不是全矢量 S 参数插损"),
        @("V3.2 分光不均衡","约 2.8×10⁻¹³ dB","当前对称模型与数值设置下")
    ) @(135,130,195) $true | Out-Null
    Add-Callout $doc "最重要的版本结论不是「插损变小了」，而是 V3.2 将功率提取从纯空间窗口积分升级为对 BPM 复数场的端口模式投影，使结果更接近端口模功率的物理定义；但端口模式仍是 Gaussian 近似。"

    Add-PageBreak $doc
    Add-Para $doc "五、模式求解与 MMI 参数优化" "标题 1" 8 | Out-Null
    Add-Para $doc "5.1 二维标量有限差分模式求解" "标题 2" 5 | Out-Null
    Add-Para $doc "V2.5 起，平台不再仅使用经验 neff，而是根据 SOI 波导折射率截面离散标量 Helmholtz 方程并求解本征值 β²，进而得到 neff=β/k0、基模场分布、约束因子和模式面积。该模块为后续 MMI 优化提供统一的 neff 输入。" "正文" 6 | Out-Null
    Add-Picture $doc (Join-Path $run "mode_profile.png") "图 1　1550 nm、0.50 μm × 0.22 μm SOI 波导的标量基模强度分布" 340
    Add-Para $doc "5.2 MMI 宽度—长度二维优化" "标题 2" 5 | Out-Null
    Add-Para $doc "优化器以快速 surrogate 响应模型进行二维扫描，选择分光比接近 50:50、总功率接近 1 的候选结构；模式求解得到的 neff 被用于初始长度估算和响应计算。该步骤负责快速搜索，不等同于全波电磁优化。" "正文" 6 | Out-Null
    Add-Picture $doc (Join-Path $run "width_length_heatmap.png") "图 2　MMI 宽度—长度二维目标函数热力图；最新运行最优点 W=2.449 μm、L=5.307 μm" 410

    Add-PageBreak $doc
    Add-Para $doc "六、BPM 传播验证与 V3.1 校准" "标题 1" 8 | Out-Null
    Add-Para $doc "6.1 二维标量 BPM" "标题 2" 5 | Out-Null
    Add-Para $doc "V3.0 新增 split-step Fourier BPM，用优化后的 MMI 几何和参考 neff 计算光场沿传播方向的演化。平台同时保存传播强度图、输出截面、增强对比图和末端复数场 NPZ，为后续端口分析提供场数据。" "正文" 6 | Out-Null
    Add-Picture $doc (Join-Path $run "field_propagation_enhanced.png") "图 3　优化 MMI 结构中的二维标量 BPM 增强传播图" 430
    Add-Para $doc "6.2 为什么需要窗口敏感性校准" "标题 2" 5 | Out-Null
    Add-Para $doc "若仅在输出截面选定空间窗口并积分，收集功率会随窗口宽度显著变化。最新运行中，窗口从 0.25 μm 增至 0.70 μm 时，总收集功率从 29.06% 增至 73.38%，对应的窗口口径插损从 5.367 dB 变为 1.344 dB。因此，V3.1 明确将该值命名为 window_based_insertion_loss_db，并加入敏感性分析，避免把窗口选择误解为器件固有损耗。" "正文" 6 | Out-Null
    Add-Picture $doc (Join-Path $run "output_window_sensitivity.png") "图 4　输出功率与窗口宽度的敏感性；说明窗口积分不是严格的端口功率定义" 410
    Add-Para $doc "6.3 Surrogate 与 BPM 的关系" "标题 2" 5 | Out-Null
    Add-Para $doc "Surrogate 用于快速搜索几何参数，BPM 用于观察传播场并检查趋势；两者并非同一物理量的严格数值对照。当前平台将差异显式记录在 model_comparison_result.json 中，汇报时应将其表述为「多层模型协同与校准」，而不是「BPM 证明了 surrogate 数值完全正确」。" "正文" 6 | Out-Null

    Add-PageBreak $doc
    Add-Para $doc "七、V3.2 端口模式重叠分析" "标题 1" 8 | Out-Null
    Add-Para $doc "V3.2 在两个输出端口中心构建归一化 Gaussian 模式，并将 BPM 输出端的复数场分别投影到两个端口模式上。与只看空间窗口内能量相比，重叠积分同时考虑了场的幅度与相位匹配，因此更具有端口模式含义。" "正文" 6 | Out-Null
    Add-Picture $doc (Join-Path $run "field_output_profile_with_modes.png") "图 5　BPM 输出场与两个简化 Gaussian 端口模式的位置关系" 430
    Add-Picture $doc (Join-Path $run "mode_overlap_comparison.png") "图 6　Surrogate、窗口积分与端口模式重叠三种功率口径对比" 390
    Add-Table $doc @(
        @("口径","P1","P2","总功率/含义"),
        @("Surrogate","0.5001","0.4999","快速优化响应，近似总功率 1"),
        @("BPM 窗口积分","0.2049","0.2049","总收集 0.4098；依赖 0.35 μm 窗口"),
        @("V3.2 模式重叠","0.4217","0.4217","总重叠 0.8434；等效插损 0.740 dB")
    ) @(110,70,70,205) $true | Out-Null
    Add-Callout $doc "V3.2 的结果可作为从「空间采样」走向「端口模式功率」的过渡版本。下一步应使用真实波导本征模式替换 Gaussian 端口模式，并在多波长点上形成等效 S21/S31 趋势。"

    Add-Para $doc "八、GDS、网页与结果交付" "标题 1" 8 | Out-Null
    Add-Para $doc "8.1 版图生成" "标题 2" 5 | Out-Null
    Add-Para $doc "平台调用 gdsfactory 生成 1×2 MMI 的 GDS 文件，并同步生成 PNG 版图预览。当前 GDS 用于展示参数到版图的自动映射，尚未接入特定代工 PDK 的层映射、DRC 和可制造性签核。" "正文" 6 | Out-Null
    Add-Picture $doc (Join-Path $run "layout_preview.png") "图 7　最新优化参数对应的 1×2 MMI 版图预览" 390
    Add-Para $doc "8.2 网页端能力" "标题 2" 5 | Out-Null
    Add-Bullets $doc @(
        "输入自然语言设计需求并解析为结构化参数。",
        "确认或修改工作波长、波导尺寸、MMI 扫描范围等参数。",
        "运行完整设计流程，并按模块展示模式、优化、波长、BPM、校准和 V3.2 重叠结果。",
        "下载 JSON、PNG、GDS、中文报告和完整 ZIP 结果包。"
    )
    Add-Para $doc "8.3 单次运行的主要交付文件" "标题 2" 5 | Out-Null
    Add-Table $doc @(
        @("类别","代表文件","用途"),
        @("输入与参数","design_spec.json、physical_params.json","记录需求和材料/物理参数"),
        @("模式","mode_result.json、index_profile.png、mode_profile.png、neff_vs_width.png","记录模式求解与宽度扫描"),
        @("优化与波长","optimization_result.json、length_sweep.png、width_length_heatmap.png、wavelength_*.png/json","记录最优参数与带宽趋势"),
        @("传播与校准","propagation_result.json、field_propagation*.png、output_window_sensitivity*.png/json、model_comparison*.png/json","记录传播场、窗口敏感性和模型比较"),
        @("端口模式","bpm_final_field_data.npz、mode_overlap_result.json、mode_overlap_comparison.png、field_output_profile_with_modes.png","记录 V3.2 模式重叠"),
        @("版图与交付","mmi1x2_demo.gds、layout_preview.png、report.md、run_log.txt、ai_pic_demo_results.zip","版图、报告、追踪与归档")
    ) @(90,205,165) $true | Out-Null

    Add-PageBreak $doc
    Add-Para $doc "九、安装、启动与操作说明" "标题 1" 8 | Out-Null
    Add-Para $doc "9.1 推荐环境" "标题 2" 5 | Out-Null
    Add-Bullets $doc @(
        "Windows 10/11；Python 3.11；VS Code。",
        "项目自带 .venv 虚拟环境时优先使用；主要依赖见 requirements.txt。",
        "主要第三方库：numpy、scipy、matplotlib、pandas、streamlit、gdsfactory、pydantic。"
    )
    Add-Para $doc "9.2 命令行运行" "标题 2" 5 | Out-Null
    $p = Add-Para $doc ".\.venv\Scripts\Activate.ps1`npython run_demo.py" "正文" 8
    $p.Range.Font.Name = "Consolas"; $p.Range.Font.NameFarEast = "等线"; $p.Range.Font.Size = 9.5; $p.Range.ParagraphFormat.FirstLineIndent = 0
    Add-Para $doc "每次运行会创建独立目录 outputs/run_时间戳，完成后可执行 python tools/check_latest_run.py 检查结果完整性。" "正文" 6 | Out-Null
    Add-Para $doc "9.3 网页端运行" "标题 2" 5 | Out-Null
    $p = Add-Para $doc "streamlit run app.py`n# 或`npython -m streamlit run app.py" "正文" 8
    $p.Range.Font.Name = "Consolas"; $p.Range.Font.Size = 9.5; $p.Range.ParagraphFormat.FirstLineIndent = 0
    Add-Para $doc "启动后访问 http://localhost:8501。Windows 用户也可双击 start_demo.bat。" "正文" 6 | Out-Null
    Add-Para $doc "9.4 推荐网页演示步骤" "标题 2" 5 | Out-Null
    Add-Numbered $doc @(
        "输入：请设计一个工作波长为 1550 nm、SOI 平台、目标 50:50 分光的 1×2 MMI 分束器。",
        "点击解析需求，展示从自然语言到 DesignSpec JSON 的转换。",
        "运行完整设计，先展示模式场和 neff，再展示宽度—长度优化结果。",
        "展示 BPM 传播图，说明这是二维标量传播近似。",
        "展示窗口敏感性图，解释为什么简单空间窗口不能直接等同于严格插损。",
        "展示 V3.2 模式重叠对比，强调从窗口积分到模式投影的升级。",
        "最后展示 GDS、中文报告和 ZIP 下载，证明闭环和可交付性。"
    )

    Add-Para $doc "十、建议的汇报话术（约 8 分钟）" "标题 1" 8 | Out-Null
    Add-Table $doc @(
        @("时间","展示内容","建议表述"),
        @("0:00–0:45","定位与结论","这不是问答机器人，而是一个可替换求解器的 PIC 自动化设计骨架；当前已升级到 V3.2。"),
        @("0:45–2:00","完整流程","从需求、模式、优化、传播到 GDS 和报告，单次运行自动归档。"),
        @("2:00–3:20","模式与优化","neff 来自二维标量有限差分基模，不再是固定经验值；快速模型负责参数搜索。"),
        @("3:20–5:00","BPM 与校准","BPM 给出传播场；窗口敏感性揭示简单积分对测量窗口的依赖。"),
        @("5:00–6:20","V3.2 升级","把末端复数场投影到两个端口模式，功率定义更接近端口模口径。"),
        @("6:20–7:15","工程闭环","现场展示 GDS、报告、日志和 ZIP，说明结果可复现和可交付。"),
        @("7:15–8:00","边界与下一步","当前仍是标量近似；下一步用真实本征模式和高保真求解器形成 S 参数趋势。")
    ) @(65,105,290) $true | Out-Null

    Add-Para $doc "十一、模型边界与结果解释原则" "标题 1" 8 | Out-Null
    Add-Table $doc @(
        @("项目","当前状态","正确表述","不可表述为"),
        @("模式求解","二维标量有限差分","比经验 neff 更物理的近似基模","全矢量 FDE/FEM"),
        @("传播","二维标量 BPM","器件内部传播趋势与场可视化","严格 FDTD/FEM/EME"),
        @("快速优化","Surrogate 响应模型","几何参数的快速预搜索","全波最优设计"),
        @("窗口插损","空间窗口积分","指定窗口下的收集功率估计","器件固有插入损耗"),
        @("模式重叠","Gaussian 端口模式投影","更具模式意识的等效端口功率","全矢量本征模 S 参数"),
        @("GDS","参数化示例版图","自动版图闭环和接口验证","已通过 PDK/DRC 的流片版图")
    ) @(75,110,145,130) $true | Out-Null
    Add-Bullets $doc @(
        "所有优化、带宽和功率结果均需通过更高保真仿真或实验进一步验证。",
        "Surrogate、窗口积分和模式重叠属于不同物理口径，不应只比较数值大小而忽略定义。",
        "当前对称分光的极小不均衡主要反映模型与几何对称性，不代表制造偏差下仍能保持同等指标。",
        "本平台当前最可靠的成果是自动化流程、模块接口、结果追踪与逐级增强的验证方法。"
    )

    Add-Para $doc "十二、后续研究路线" "标题 1" 8 | Out-Null
    Add-Table $doc @(
        @("阶段","建议版本","目标","关键工作"),
        @("近期","V3.5","宽带端口指标趋势","在多个波长执行模式重叠，形成等效 S21/S31 和带宽趋势"),
        @("中期","V4.0","工艺约束与版图签核接口","接入 PDK 层映射、LayerStack、DRC 和制造偏差扫描"),
        @("中期","V4.x","高保真求解闭环","用真实波导本征模式替代 Gaussian；接入 Meep、Tidy3D、FEMWELL、Lumerical 或 COMSOL"),
        @("远期","V5.0","AI Workflow / Agent 化","让 Agent 管理需求解析、工具调用、收敛判断、结果审计和多轮优化"),
        @("扩展","后续器件库","验证平台通用性","加入 directional coupler、ring resonator、grating coupler 等模板")
    ) @(60,60,125,225) $true | Out-Null
    Add-Callout $doc "建议下一阶段优先做「真实端口本征模式 + 多波长重叠」，因为它能直接承接 V3.2 的场数据与接口，又能把当前最关键的结果口径向 S 参数分析推进。"

    Add-Para $doc "十三、阶段性结论" "标题 1" 8 | Out-Null
    Add-Para $doc "当前项目已经形成可运行、可展示、可复现、可扩展的 AI 光子芯片设计平台 Demo V3.2。相比旧版说明书，平台的核心进展是：模式参数来自二维标量有限差分求解；优化后的 MMI 通过二维标量 BPM 展示传播场；窗口敏感性和模型比较使结果解释更严谨；端口模式重叠让功率提取从空间窗口走向模式投影；GDS、网页、中文报告和结果包继续保持完整闭环。" "正文" 6 | Out-Null
    Add-Para $doc "因此，本阶段成果可以定义为「面向研究与教学的多层物理模型驱动 PIC 自动化设计原型」。它已经具备继续接入高保真求解器、PDK/DRC 和 AI Agent 的工程基础，但尚不能代替全矢量电磁仿真和流片签核。" "正文" 6 | Out-Null

    Add-Para $doc "附录 A：项目主要目录" "标题 1" 8 | Out-Null
    $p = Add-Para $doc @"
AI_PIC_Demo/
├─ app.py                 Streamlit 网页入口
├─ run_demo.py            命令行完整流程
├─ core/                  参数、模式、优化、传播、重叠、报告与打包
├─ layout/                GDS 与版图预览
├─ tools/                 完整性检查与输出清理
├─ docs/versions/         版本说明
├─ examples/              代表性示例说明
└─ outputs/run_*/         单次运行结果
"@ "正文" 6
    $p.Range.Font.Name = "Consolas"; $p.Range.Font.Size = 9; $p.Range.ParagraphFormat.FirstLineIndent = 0

    # 页眉页脚
    $section = $doc.Sections.Item(1)
    $header = $section.Headers.Item(1).Range
    $header.Text = "AI 光子芯片设计平台 Demo V3.2｜项目介绍与使用说明书"
    $header.Font.NameFarEast = "等线"; $header.Font.Size = 8.5; $header.Font.Color = 8421504
    $header.ParagraphFormat.Alignment = 2
    $footer = $section.Footers.Item(1)
    $footer.Range.Text = "内部汇报材料　｜　2026-07-06　｜　"
    $footer.Range.Font.NameFarEast = "等线"; $footer.Range.Font.Size = 8.5; $footer.Range.Font.Color = 8421504
    $footer.Range.ParagraphFormat.Alignment = 1
    $footer.PageNumbers.Add(1, $true) | Out-Null

    $toc.Update() | Out-Null
    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    if (Test-Path $OutputPath) { Remove-Item -LiteralPath $OutputPath -Force }
    $doc.SaveAs2($OutputPath, 16)
    $pages = $doc.ComputeStatistics(2)
    $tables = $doc.Tables.Count
    $images = $doc.InlineShapes.Count
    $paras = $doc.Paragraphs.Count
    $doc.Close(0)
    $word.Quit()
    "Created: $OutputPath"
    "Pages: $pages; Tables: $tables; Images: $images; Paragraphs: $paras"
} catch {
    if ($doc) { try { $doc.Close(0) } catch {} }
    try { $word.Quit() } catch {}
    throw
}
