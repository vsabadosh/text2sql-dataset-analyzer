#!/bin/bash

# Скрипт для конвертації SVG діаграм у PNG високої якості
# Використовує Inkscape для конвертації

# Перевірка наявності Inkscape
if ! command -v inkscape &> /dev/null; then
    echo "❌ Inkscape не встановлено!"
    echo ""
    echo "Встановіть Inkscape:"
    echo "  macOS: brew install inkscape"
    echo "  Ubuntu/Debian: sudo apt-get install inkscape"
    echo "  Windows: завантажте з https://inkscape.org/"
    echo ""
    echo "Альтернативно, використайте онлайн конвертер:"
    echo "  https://cloudconvert.com/svg-to-png"
    exit 1
fi

echo "🎨 Конвертація SVG діаграм у PNG (300 DPI)..."
echo ""

# DPI для високої якості друку
DPI=300

# Масив файлів для конвертації
declare -a files=(
    "01_system_architecture.svg"
    "02_data_flow.svg"
    "03_llm_judge_architecture.svg"
    "04_protocol_based_architecture.svg"
)

# Конвертація кожного файлу
for svg_file in "${files[@]}"; do
    if [ -f "$svg_file" ]; then
        png_file="${svg_file%.svg}.png"
        echo "📄 Конвертую: $svg_file → $png_file"
        
        inkscape "$svg_file" \
            --export-type=png \
            --export-dpi=$DPI \
            --export-filename="$png_file" \
            2>/dev/null
        
        if [ $? -eq 0 ]; then
            # Отримати розмір файлу
            size=$(du -h "$png_file" | cut -f1)
            echo "   ✅ Готово! Розмір: $size"
        else
            echo "   ❌ Помилка конвертації"
        fi
    else
        echo "   ⚠️  Файл не знайдено: $svg_file"
    fi
    echo ""
done

echo "✨ Конвертація завершена!"
echo ""
echo "Створено PNG файли з роздільною здатністю $DPI DPI"
echo "Ці файли готові для вставки у Word документ"
echo ""
echo "Наступні кроки:"
echo "  1. Відкрийте Word документ"
echo "  2. Вставте PNG файли замість placeholder'ів [ТУТ БУДЕ РИСУНОК...]"
echo "  3. Налаштуйте ширину зображень ~16-17 см"
echo "  4. Додайте підписи до рисунків"
echo ""
echo "Докладніше: Article/DIAGRAM_INTEGRATION_GUIDE.md"

