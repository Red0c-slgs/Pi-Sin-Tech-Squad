from PIL import Image
import logging
import os


async def create_icon(temp_dir: str, filename: str) -> str:
    """
    Создает квадратную иконку 100x100 пикселей из исходного изображения
    с сохранением пропорций и обрезкой при необходимости

    :param temp_dir: Путь к изображению в tmp
    :param filename: Имя изображения
    """
    image_path = os.path.join(temp_dir, filename)
    try:
        with Image.open(image_path) as img:
            # Конвертируем в RGB если нужно (для PNG с прозрачностью)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Определяем размеры для ресайза с сохранением пропорций
            width, height = img.size
            min_side = min(width, height)

            # Обрезаем до центрального квадрата
            left = (width - min_side) / 2
            top = (height - min_side) / 2
            right = (width + min_side) / 2
            bottom = (height + min_side) / 2
            img = img.crop((left, top, right, bottom))

            # Ресайз до 100x100
            img.thumbnail((100, 100))

            # Сохраняем в temp
            save_path = os.path.join(temp_dir, "icon_"+filename)
            img.save(save_path)
            return save_path

    except Exception as e:
        logging.error(f"Error creating thumbnail: {str(e)}")
        raise ValueError("Could not process image") from e