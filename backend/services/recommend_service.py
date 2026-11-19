"""Recommendation and product advisor service for Voltix TechStore.

Implements rule-based multi-factor scoring and constraint filtering.
"""

from typing import List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from models.orm import Product, Category
from models.schemas import RecommendRequest, RecommendationItem
from services.product_service import calculate_sale_price, orm_to_product_public


class RecommendService:
    @staticmethod
    def get_recommendations(db: Session, request: RecommendRequest) -> List[RecommendationItem]:
        """
        Recommends top 3 products based on:
        1. Strict SQL filtering by category and budget (using calculated sale_price).
        2. Multi-factor rule-based scoring:
           - Use case matching (+30)
           - Priority attribute boost (+30 for category-specific priorities)
           - GPU bonus (+15 only if use_case == 'gaming' or priority == 'gpu')
           - Stock availability bonus (+10 if in stock)
           - Customer rating (+5) and discount (+5) bonuses
        3. Normalization: raw score divided by maximum possible score for the request (0-100%).
        4. Returns Top-3 sorted by score descending, with reasons in Russian.
        """
        cat_slug = request.category.strip().lower()

        # Step 1: SQL Query filtered by category
        products = (
            db.query(Product)
            .options(joinedload(Product.category_rel), joinedload(Product.reviews))
            .join(Product.category_rel)
            .filter(Category.slug == cat_slug)
            .all()
        )

        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"В категории '{cat_slug}' пока нет доступных товаров.",
            )

        # Calculate minimum sale price in the category
        products_with_prices = [
            (p, calculate_sale_price(float(p.price), float(p.discount_percentage or 0.0)))
            for p in products
        ]
        min_cat_price = min(price for _, price in products_with_prices)

        if request.budget < min_cat_price:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Бюджет слишком мал. Минимальная цена в категории '{cat_slug}' — ${min_cat_price:.2f}. Пожалуйста, увеличьте бюджет.",
            )

        # Filter candidates strictly within budget
        budget_candidates = [(p, price) for p, price in products_with_prices if price <= request.budget]

        if not budget_candidates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Подходящих товаров в категории '{cat_slug}' в пределах бюджета ${request.budget:.2f} не найдено.",
            )

        # Step 2: Scoring each candidate
        use_case_req = request.use_case.strip().lower()
        priority_req = request.priority.strip().lower()

        # Compute maximum possible points for this specific query
        has_gpu_relevance = (use_case_req == "gaming" or priority_req == "gpu")
        max_possible_score = 20.0 + 30.0 + 30.0 + (15.0 if has_gpu_relevance else 0.0) + 10.0 + 10.0

        scored_items: List[Tuple[float, List[str], Product]] = []

        for p, final_price in budget_candidates:
            score = 20.0  # Base qualifying points
            reasons = []

            # 1. Budget fit reason
            savings = round(float(p.price) - final_price, 2)
            if savings > 0:
                reasons.append(f"Вписывается в бюджет ${request.budget:.0f} с учетом скидки ${savings:.2f}")
            else:
                reasons.append(f"Отличная цена ${final_price:.2f} в рамках бюджета ${request.budget:.0f}")

            # 2. Use-case match (+30)
            prod_cases = (p.use_cases or "").lower()
            prod_desc = (p.description or "").lower()
            if use_case_req in prod_cases or use_case_req in prod_desc:
                score += 30.0
                if use_case_req == "gaming":
                    reasons.append("Оптимизирован для гейминга и высоких графических нагрузок")
                elif use_case_req in ("dev", "office", "work"):
                    reasons.append("Идеально подходит для рабочих задач, кода и офисных приложений")
                elif use_case_req == "study":
                    reasons.append("Отличное решение для учебы, лекций и подготовки проектов")
                elif use_case_req == "photo":
                    reasons.append("Продвинутые возможности фото- и видеосъемки высокого качества")
                elif use_case_req == "multimedia":
                    reasons.append("Превосходный дисплей и звук для фильмов, чтения и медиа")
                elif use_case_req == "battery":
                    reasons.append("Рассчитан на интенсивную автономную работу вдали от зарядки")
                else:
                    reasons.append(f"Подходит для сценария: {request.use_case}")

            # 3. Category-specific Priority boost (+30 max)
            if cat_slug == "laptops":
                if priority_req == "memory":
                    if p.ram_gb and p.ram_gb >= 16:
                        score += 20.0
                        reasons.append(f"Большой объём оперативной памяти ({p.ram_gb} ГБ) для многозадачности")
                    elif p.ram_gb and p.ram_gb >= 8:
                        score += 10.0
                        reasons.append(f"Достаточный объём оперативной памяти ({p.ram_gb} ГБ)")

                    if p.storage_gb and p.storage_gb >= 512:
                        score += 10.0
                        reasons.append(f"Вместительный накопитель на {p.storage_gb} ГБ")

                elif priority_req == "weight":
                    if p.weight_kg and p.weight_kg <= 1.5:
                        score += 30.0
                        reasons.append(f"Ультралегкий корпус ({p.weight_kg} кг) — максимальная мобильность")
                    elif p.weight_kg and p.weight_kg <= 1.9:
                        score += 15.0
                        reasons.append(f"Умеренный вес ({p.weight_kg} кг)")

                elif priority_req == "battery":
                    if p.battery_mah and p.battery_mah >= 65000:
                        score += 30.0
                        reasons.append("Энергоэффективная батарея для долгого рабочего дня без подзарядки")
                    elif p.battery_mah:
                        score += 15.0
                        reasons.append("Надёжный аккумулятор для повседневной работы")

                elif priority_req == "gpu":
                    if p.gaming_gpu:
                        score += 30.0
                        reasons.append("Мощный дискретный графический процессор для высоких FPS")

            elif cat_slug == "smartphones":
                if priority_req == "camera":
                    if p.camera_mp and p.camera_mp >= 48:
                        score += 30.0
                        reasons.append(f"Основная камера высокого разрешения {p.camera_mp} Мп")
                    elif p.camera_mp:
                        score += 15.0
                        reasons.append(f"Качественная камера {p.camera_mp} Мп")

                elif priority_req == "battery":
                    if p.battery_mah and p.battery_mah >= 5000:
                        score += 30.0
                        reasons.append(f"Емкий аккумулятор {p.battery_mah} мАч обеспечивает 2 дня работы")
                    elif p.battery_mah and p.battery_mah >= 4000:
                        score += 15.0
                        reasons.append(f"Хорошая автономность с аккумулятором {p.battery_mah} мАч")

                elif priority_req == "memory":
                    if p.ram_gb and p.ram_gb >= 12:
                        score += 15.0
                        reasons.append(f"Флагманский объём RAM ({p.ram_gb} ГБ)")
                    elif p.ram_gb and p.ram_gb >= 8:
                        score += 10.0
                        reasons.append(f"Оптимальный объём RAM ({p.ram_gb} ГБ)")

                    if p.storage_gb and p.storage_gb >= 256:
                        score += 15.0
                        reasons.append(f"Просторный накопитель на {p.storage_gb} ГБ")

                elif priority_req == "weight":
                    if p.weight_kg and p.weight_kg <= 0.18:
                        score += 30.0
                        reasons.append(f"Легкий и тонкий корпус ({int(p.weight_kg * 1000)} г)")
                    elif p.weight_kg and p.weight_kg <= 0.20:
                        score += 15.0
                        reasons.append(f"Эргономичный вес ({int(p.weight_kg * 1000)} г)")

            elif cat_slug == "tablets":
                if priority_req == "screen":
                    score += 30.0
                    reasons.append("Качественный Retina/OLED дисплей с высокой плотностью пикселей")
                elif priority_req == "battery":
                    if p.battery_mah and p.battery_mah >= 7000:
                        score += 30.0
                        reasons.append("Емкая батарея для целого дня просмотра видео и работы")
                    else:
                        score += 20.0
                        reasons.append("Достойное время работы без подзарядки")
                elif priority_req == "memory":
                    if p.ram_gb and p.ram_gb >= 8:
                        score += 15.0
                        reasons.append(f"Быстрая оперативная память {p.ram_gb} ГБ")
                    if p.storage_gb and p.storage_gb >= 128:
                        score += 15.0
                        reasons.append(f"Вместительное хранилище {p.storage_gb} ГБ")
                elif priority_req == "weight":
                    if p.weight_kg and p.weight_kg <= 0.5:
                        score += 30.0
                        reasons.append(f"Легкий планшет ({int(p.weight_kg * 1000)} г) — удобно держать в одной руке")

            # 4. Discrete GPU bonus (+15) — ONLY applied when gaming or gpu is requested!
            if p.gaming_gpu and has_gpu_relevance:
                score += 15.0
                reasons.append("Оснащен дискретной игровой видеокартой для высокой производительности")

            # 5. Stock availability bonus (+10)
            if p.stock > 0:
                score += 10.0
                reasons.append(f"В наличии на складе ({p.stock} шт.)")
            else:
                score -= 10.0

            # 6. Customer rating (+5) & discount (+5)
            if p.rating >= 4.5:
                score += 5.0
                reasons.append(f"Высокий рейтинг покупателей ({p.rating} ★)")

            if p.discount_percentage >= 5.0:
                score += 5.0
                reasons.append(f"Выгодное предложение со скидкой {int(p.discount_percentage)}%")

            # Normalize score strictly to 0..100
            normalized_score = round(min(100.0, max(0.0, (score / max_possible_score) * 100.0)), 1)
            scored_items.append((normalized_score, reasons, p))

        # Sort by score descending
        scored_items.sort(key=lambda x: x[0], reverse=True)

        top_3 = scored_items[:3]
        if not top_3:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Не найдено подходящих рекомендаций для категории '{cat_slug}'.",
            )

        results: List[RecommendationItem] = []
        for score_val, reason_list, prod in top_3:
            pub = orm_to_product_public(prod)
            item = RecommendationItem(
                **pub.model_dump(),
                score=score_val,
                reasons=reason_list,
            )
            results.append(item)

        return results


recommend_service = RecommendService()
