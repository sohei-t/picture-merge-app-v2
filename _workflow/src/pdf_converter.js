#!/usr/bin/env node

/**
 * Markdown to PDF Converter
 * Uses puppeteer for high-quality PDF generation
 */

const fs = require('fs').promises;
const path = require('path');
const { marked } = require('marked');
const puppeteer = require('puppeteer');

// PDF変換設定
const PDF_OPTIONS = {
    format: 'A4',
    margin: {
        top: '20mm',
        right: '20mm',
        bottom: '20mm',
        left: '20mm'
    },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div style="font-size: 10px; text-align: center; width: 100%;"></div>',
    footerTemplate: '<div style="font-size: 10px; text-align: center; width: 100%;"><span class="pageNumber"></span> / <span class="totalPages"></span></div>'
};

// CSSスタイル（日本語フォント対応）
const CSS_STYLE = `
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');

    body {
        font-family: 'Noto Sans JP', 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
        line-height: 1.8;
        color: #333;
        max-width: 100%;
        margin: 0;
        padding: 20px;
        font-size: 11pt;
    }

    h1 {
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
        margin-top: 40px;
        margin-bottom: 20px;
        font-size: 24pt;
        page-break-before: auto;
    }

    h1:first-child {
        margin-top: 0;
    }

    h2 {
        color: #34495e;
        border-bottom: 1px solid #bdc3c7;
        padding-bottom: 5px;
        margin-top: 30px;
        margin-bottom: 15px;
        font-size: 18pt;
    }

    h3 {
        color: #555;
        margin-top: 25px;
        margin-bottom: 10px;
        font-size: 14pt;
    }

    table {
        border-collapse: collapse;
        width: 100%;
        margin: 15px 0;
    }

    table th {
        background-color: #3498db;
        color: white;
        padding: 10px;
        text-align: left;
        font-weight: bold;
    }

    table td {
        border: 1px solid #ddd;
        padding: 10px;
    }

    table tr:nth-child(even) {
        background-color: #f9f9f9;
    }

    code {
        background-color: #f4f4f4;
        padding: 2px 5px;
        border-radius: 3px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 10pt;
    }

    pre {
        background-color: #f8f8f8;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        overflow-x: auto;
        font-size: 10pt;
    }

    pre code {
        background-color: transparent;
        padding: 0;
    }

    blockquote {
        border-left: 4px solid #3498db;
        padding-left: 15px;
        margin-left: 0;
        color: #666;
        font-style: italic;
    }

    ul, ol {
        margin-left: 20px;
        margin-bottom: 15px;
    }

    li {
        margin-bottom: 5px;
    }

    a {
        color: #3498db;
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    /* ページ番号のスタイル */
    .page-break {
        page-break-after: always;
    }

    /* 承認欄のスタイル */
    .approval-table {
        margin-top: 50px;
    }

    .approval-table td {
        height: 40px;
        vertical-align: bottom;
    }

    /* チェックマークの表示 */
    input[type="checkbox"] {
        transform: scale(1.2);
        margin-right: 5px;
    }

    /* 印刷時の最適化 */
    @media print {
        body {
            font-size: 10pt;
        }

        h1 {
            font-size: 20pt;
        }

        h2 {
            font-size: 16pt;
        }

        h3 {
            font-size: 12pt;
        }
    }
</style>
`;

/**
 * MarkdownファイルをPDFに変換
 */
async function convertMarkdownToPDF(mdFilePath, pdfFilePath) {
    try {
        // Markdownファイルを読み込み
        const markdown = await fs.readFile(mdFilePath, 'utf-8');

        // MarkdownをHTMLに変換
        const htmlContent = marked(markdown);

        // 完全なHTMLドキュメントを作成
        const fullHtml = `
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${path.basename(mdFilePath, '.md')}</title>
    ${CSS_STYLE}
</head>
<body>
    ${htmlContent}
</body>
</html>
        `;

        // Puppeteerでブラウザを起動
        const browser = await puppeteer.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        const page = await browser.newPage();

        // HTMLを設定
        await page.setContent(fullHtml, {
            waitUntil: 'networkidle0'
        });

        // PDFを生成
        await page.pdf({
            path: pdfFilePath,
            ...PDF_OPTIONS
        });

        await browser.close();

        console.log(`✅ 変換完了: ${path.basename(pdfFilePath)}`);
        return true;
    } catch (error) {
        console.error(`❌ 変換エラー (${path.basename(mdFilePath)}):`, error.message);
        return false;
    }
}

/**
 * ディレクトリ内のすべてのMarkdownファイルをPDFに変換
 */
async function convertAllMarkdownFiles(directory) {
    try {
        const files = await fs.readdir(directory);
        const mdFiles = files.filter(file => file.endsWith('.md'));

        if (mdFiles.length === 0) {
            console.log('変換するMarkdownファイルが見つかりません。');
            return;
        }

        console.log(`\n📄 ${mdFiles.length}個のファイルをPDFに変換します...\n`);

        let successCount = 0;
        for (const mdFile of mdFiles) {
            const mdPath = path.join(directory, mdFile);
            const pdfPath = path.join(directory, mdFile.replace('.md', '.pdf'));

            const success = await convertMarkdownToPDF(mdPath, pdfPath);
            if (success) successCount++;
        }

        console.log(`\n✨ 変換完了: ${successCount}/${mdFiles.length} ファイル`);

    } catch (error) {
        console.error('エラー:', error);
        process.exit(1);
    }
}

/**
 * package.jsonの依存関係を確認
 */
async function checkDependencies() {
    try {
        require('marked');
        require('puppeteer');
        return true;
    } catch (error) {
        console.log('\n⚠️  必要なパッケージがインストールされていません。');
        console.log('以下のコマンドを実行してください:\n');
        console.log('npm install marked puppeteer');
        console.log('\nまたは:\n');
        console.log('npm install -g marked puppeteer\n');
        return false;
    }
}

/**
 * メイン処理
 */
async function main() {
    // 依存関係の確認
    const depsOk = await checkDependencies();
    if (!depsOk) {
        process.exit(1);
    }

    // コマンドライン引数の処理
    const args = process.argv.slice(2);

    if (args.length === 0) {
        // デフォルト: deliverables/01_documents/
        const defaultDir = path.join(process.cwd(), 'deliverables', '01_documents');

        try {
            await fs.access(defaultDir);
            await convertAllMarkdownFiles(defaultDir);
        } catch {
            console.log('使用方法:');
            console.log('  node pdf_converter.js [ディレクトリ]');
            console.log('  node pdf_converter.js [入力.md] [出力.pdf]');
            console.log('\n例:');
            console.log('  node pdf_converter.js deliverables/01_documents/');
            console.log('  node pdf_converter.js README.md README.pdf');
        }
    } else if (args.length === 1) {
        // ディレクトリ指定
        const dir = args[0];
        const stats = await fs.stat(dir);

        if (stats.isDirectory()) {
            await convertAllMarkdownFiles(dir);
        } else if (dir.endsWith('.md')) {
            // 単一ファイル（出力名自動）
            const pdfPath = dir.replace('.md', '.pdf');
            await convertMarkdownToPDF(dir, pdfPath);
        }
    } else if (args.length === 2) {
        // 入力と出力を指定
        const [input, output] = args;
        await convertMarkdownToPDF(input, output);
    }
}

// スクリプト実行
if (require.main === module) {
    main().catch(console.error);
}

module.exports = {
    convertMarkdownToPDF,
    convertAllMarkdownFiles
};