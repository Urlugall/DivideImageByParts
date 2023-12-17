from PIL import Image
import numpy as np
import os

def find_connected_component(img, start, visited, alpha_threshold):
    """ Найти связанный компонент, начиная с пикселя start """
    stack = [start]
    component = []

    while stack:
        x, y = stack.pop()
        if (x, y) in visited:
            continue

        visited.add((x, y))
        component.append((x, y))

        # Проверить соседние пиксели
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < img.shape[1] and 0 <= ny < img.shape[0]:
                    # Проверяем, не является ли пиксель "пустым" на основе альфа-канала
                    if img[ny, nx, 3] > alpha_threshold:
                        stack.append((nx, ny))

    return component


def save_component_as_image(component, original_image_size, image_data, output_path):
    # Создаем новое изображение с прозрачным фоном и исходными размерами
    component_image = Image.new('RGBA', original_image_size, color=(0, 0, 0, 0))
    component_pixels = np.array(component_image)
    
    # Находим границы компонента
    min_x = min(x for x, _ in component)
    min_y = min(y for _, y in component)
    
    # Копируем пиксели компонента в новое изображение
    for x, y in component:
        # Если пиксель не прозрачный, красим его в белый
        if image_data[y, x][3] > 0:  # Альфа канал больше 0
            component_pixels[y, x] = (255, 255, 255, image_data[y, x][3])
        else:
            component_pixels[y, x] = image_data[y, x]
    
    # Создаем подизображение вокруг компонента
    #component_subimage = component_pixels[min_y:max(y for _, y in component)+1, min_x:max(x for x, _ in component)+1]
    
    # Преобразуем обратно в объект изображения PIL и сохраняем
    Image.fromarray(component_pixels).save(output_path)



def split_sprite(image_path, output_folder, min_size=10, alpha_threshold=0):
    print(f"Загрузка изображения из {image_path}")
    with Image.open(image_path) as image:
        if image.mode in ['P', 'L']:
            # Преобразование изображения в RGBA, если оно не в этом формате
            image = image.convert('RGBA')
        
        image_data = np.array(image)
        # Создаем маску для пикселей, где альфа-канал выше порога
        alpha_mask = image_data[:,:,3] > alpha_threshold

    visited = set()
    components = []

    print("Начало обработки изображения...")
    for y in range(alpha_mask.shape[0]):
        for x in range(alpha_mask.shape[1]):
            if alpha_mask[y, x] and (x, y) not in visited:
                print(f"Обработка компонента в позиции: {x}, {y}")
                component = find_connected_component(image_data, (x, y), visited, alpha_threshold)
                if len(component) >= min_size:
                    components.append(component)
                    print(f"Найден компонент размером {len(component)} пикселей")

    print(f"Обработка завершена. Найдено {len(components)} компонентов.")

    original_image_size = image_data.shape[:2]

    # Сохранение каждого компонента
    for i, component in enumerate(components, 1):
        output_path = os.path.join(output_folder, f'sprite_{i}.png')
        save_component_as_image(component, original_image_size, image_data, output_path)

    print("Все компоненты сохранены.")

# Использование функции
split_sprite('C:\\Projects\\Unity\\Match and Color\\Assets\\Sprites\\Levels\\Level1\\Brown.png', 'C:\\Projects\\Unity\\Match and Color\\Assets\\Sprites\\Levels\\Level1\\Brown', min_size=30, alpha_threshold=188)
