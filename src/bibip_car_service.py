from pathlib import Path
from datetime import datetime
from decimal import Decimal

from models import Car, Model, Sale, CarStatus, CarFullInfo, ModelSaleStats


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        # Корневая папка для файлов БД
        self.root = Path(root_directory_path)
        self.root.mkdir(exist_ok=True)
        # Создаем файлы, если их нет
        for fname in ("models.txt",
                      "models_index.txt",
                      "cars.txt",
                      "cars_index.txt",
                      "sales.txt",
                      "sales_index.txt"):
            path = self.root / fname
            if not path.exists():
                path.touch()

    # Задание 1. Сохранение моделей
    def add_model(self, model: Model) -> Model:
        models_path = self.root / "models.txt"
        index_path = self.root / "models_index.txt"
        record = f"{model.id};{model.name};{model.brand}".ljust(500) + "\n"

        with open(models_path, 'a', encoding='utf-8') as f:
            f.write(record)

        lines = open(models_path, 'r', encoding='utf-8').readlines()
        entries = []
        if index_path.exists():
            for ln in open(index_path, 'r', encoding='utf-8'):
                k, n = ln.strip().split(';')
                entries.append((int(k), int(n)))
        entries.append((model.id, len(lines) - 1))
        entries.sort(key=lambda x: x[0])
        with open(index_path, 'w', encoding='utf-8') as f:
            for i, y in entries:
                f.write(f"{i};{y}\n")
        return model

    # Задание 1. Сохранение автомобилей
    def add_car(self, car: Car) -> Car:
        cars_path = self.root / "cars.txt"
        index_path = self.root / "cars_index.txt"
        record = (
            f"{car.vin};{car.model};{car.price};"
            f"{car.date_start.isoformat()};{car.status.value}".ljust(500)
            + "\n"
        )

        with open(cars_path, 'a', encoding='utf-8') as f:
            f.write(record)

        lines = open(cars_path, 'r', encoding='utf-8').readlines()
        entries = []
        if index_path.exists():
            for ln in open(index_path, 'r', encoding='utf-8'):
                k, n = ln.strip().split(';')
                entries.append((k, int(n)))
        entries.append((car.vin, len(lines) - 1))
        entries.sort(key=lambda x: x[0])
        with open(index_path, 'w', encoding='utf-8') as f:
            for i, y in entries:
                f.write(f"{i};{y}\n")
        return car

    # Задание 2. Сохранение продаж
    def sell_car(self, sale: Sale) -> Car:
        sales_path = self.root / "sales.txt"
        sales_index = self.root / "sales_index.txt"
        cars_path = self.root / "cars.txt"
        cars_index = self.root / "cars_index.txt"

        rec = (
            f"{sale.sales_number};{sale.car_vin};"
            f"{sale.sales_date.isoformat()};{sale.cost}".ljust(500) + "\n"
            )
        with open(sales_path, 'a', encoding='utf-8') as f:
            f.write(rec)
        s_lines = open(sales_path, 'r', encoding='utf-8').readlines()

        entries = []
        if sales_index.exists():
            for ln in open(sales_index, 'r', encoding='utf-8'):
                k, n = ln.strip().split(';')
                entries.append((k, int(n)))
        entries.append((sale.sales_number, len(s_lines) - 1))
        entries.sort(key=lambda x: x[0])
        with open(sales_index, 'w', encoding='utf-8') as f:
            for i, y in entries:
                f.write(f"{i};{y}\n")

        idx_map = {}
        for ln in open(cars_index, 'r', encoding='utf-8'):
            vin, idx = ln.strip().split(';')
            idx_map[vin] = int(idx)
        ln_num = idx_map.get(sale.car_vin)
        if ln_num is None:
            raise ValueError("Car not found in index")
        car_lines = open(cars_path, 'r', encoding='utf-8').readlines()
        parts = car_lines[ln_num].rstrip("\n").split(';')
        parts[4] = CarStatus.sold.value
        car_lines[ln_num] = ';'.join(parts).ljust(500) + "\n"
        with open(cars_path, 'w', encoding='utf-8') as f:
            f.writelines(car_lines)
        return Car(
            vin=sale.car_vin,
            model=int(parts[1]),
            price=Decimal(parts[2]),
            date_start=datetime.fromisoformat(parts[3]),
            status=CarStatus.sold
        )

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        cars_path = self.root / "cars.txt"
        result = []
        for ln in open(cars_path, 'r', encoding='utf-8'):
            parts = ln.rstrip("\n").split(';')
            if len(parts) < 5:
                continue
            if parts[4].strip() == status.value:
                result.append(
                    Car(vin=parts[0],
                        model=int(parts[1]),
                        price=Decimal(parts[2]),
                        date_start=datetime.fromisoformat(parts[3]),
                        status=status)
                )
        return result

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        cars_path = self.root / "cars.txt"
        cars_index = self.root / "cars_index.txt"
        models_path = self.root / "models.txt"
        models_index = self.root / "models_index.txt"
        sales_path = self.root / "sales.txt"

        idx_map = {}
        for ln in open(cars_index, 'r', encoding='utf-8'):
            k, n = ln.strip().split(';')
            idx_map[k] = int(n)
        if vin not in idx_map:
            return None

        cparts = open(
            cars_path, 'r', encoding='utf-8'
            ).readlines()[idx_map[vin]].rstrip("\n").split(';')
        price = Decimal(cparts[2])
        ds = datetime.fromisoformat(cparts[3])
        st = CarStatus(cparts[4].strip())

        mid_map = {}
        for ln in open(models_index, 'r', encoding='utf-8'):
            k, n = ln.strip().split(';')
            mid_map[int(k)] = int(n)
        mparts = open(
            models_path, 'r', encoding='utf-8'
            ).readlines()[mid_map[int(cparts[1])]].rstrip("\n").split(';')
        mname, mbrand = mparts[1].strip(), mparts[2].strip()

        sd, sc = None, None
        if st == CarStatus.sold:
            for ln in open(sales_path, 'r', encoding='utf-8'):
                sp = ln.rstrip("\n").split(';')
                if sp[1] == vin:
                    sd = datetime.fromisoformat(sp[2])
                    sc = Decimal(sp[3])
                    break
        return CarFullInfo(vin=vin,
                           car_model_name=mname,
                           car_model_brand=mbrand,
                           price=price,
                           date_start=ds,
                           status=st,
                           sales_date=sd,
                           sales_cost=sc)

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        cars_path = self.root / "cars.txt"
        idx_path = self.root / "cars_index.txt"
        lines = open(cars_path, 'r', encoding='utf-8').readlines()
        idxs = []
        for ln in open(idx_path, 'r', encoding='utf-8'):
            k, n = ln.strip().split(';')
            idxs.append((k, int(n)))
        ln_num: int | None = None
        new_idxs = []
        for i, y in idxs:
            if i == vin:
                new_idxs.append((new_vin, y))
                ln_num = y
            else:
                new_idxs.append((i, y))
        new_idxs.sort(key=lambda x: x[0])
        with open(idx_path, 'w', encoding='utf-8') as f:
            for i, y in new_idxs:
                f.write(f"{i};{y}\n")
        if ln_num is not None:
            parts = lines[ln_num].rstrip("\n").split(';')
            parts[0] = new_vin
            parts[4] = parts[4].strip()
            lines[ln_num] = ';'.join(parts).ljust(500) + "\n"
        else:
            raise ValueError("VIN не найден - не возможно обновить")
        with open(cars_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return Car(vin=new_vin,
                   model=int(parts[1]),
                   price=Decimal(parts[2]),
                   date_start=datetime.fromisoformat(parts[3]),
                   status=CarStatus(parts[4]))

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        sales_path = self.root / "sales.txt"
        idx_path = self.root / "sales_index.txt"
        cars_path = self.root / "cars.txt"
        cars_index = self.root / "cars_index.txt"

        remaining = []
        removed_vin: str | None = None

        for ln in open(sales_path, 'r', encoding='utf-8'):
            p = ln.rstrip("\n").split(';')
            if p[0] == sales_number:
                removed_vin = p[1]
            else:
                remaining.append(ln)

        with open(sales_path, 'w', encoding='utf-8') as f:
            f.writelines(remaining)

        idxs = []
        for ln in open(idx_path, 'r', encoding='utf-8'):
            k, n = ln.strip().split(';')
            if k != sales_number:
                idxs.append((k, int(n)))
        idxs.sort(key=lambda x: x[0])

        with open(idx_path, 'w', encoding='utf-8') as f:
            for i, y in idxs:
                f.write(f"{i};{y}\n")

        if removed_vin is None:
            raise ValueError("VIN не найден — невозможно\
                              добавить информацию о машине")

        car = self.get_car_info(removed_vin)
        if car is None:
            raise ValueError(f"Информация о машине\
                              с VIN {removed_vin} не найдена")

        lines = open(cars_path, 'r', encoding='utf-8').readlines()
        idx_map = {}

        for ln in open(cars_index, 'r', encoding='utf-8'):
            k, n = ln.strip().split(';')
            idx_map[k] = int(n)

        ln_num = idx_map[removed_vin]
        parts = lines[ln_num].rstrip("\n").split(';')
        parts[4] = CarStatus.available.value
        lines[ln_num] = ';'.join(parts).ljust(500) + "\n"

        with open(cars_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return Car

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        cars = open(self.root / "cars.txt", 'r', encoding='utf-8').readlines()
        sales = open(
            self.root / "sales.txt", 'r', encoding='utf-8'
            ).readlines()
        vin2model = {}
        for ln in cars:
            parts = ln.rstrip("\n").split(';')
            vin2model[parts[0]] = int(parts[1])
        counts: dict[int, int] = {}
        for ln in sales:
            parts = ln.rstrip("\n").split(';')
            m = vin2model.get(parts[1])
            if m is not None:
                counts[m] = counts.get(m, 0) + 1
        price_sum: dict[int, Decimal] = {}
        count_sum: dict[int, int] = {}
        for ln in cars:
            parts = ln.rstrip("\n").split(';')
            m = int(parts[1])
            price_sum[m] = price_sum.get(m, Decimal(0)) + Decimal(parts[2])
            count_sum[m] = count_sum.get(m, 0) + 1
        avg = {m: price_sum[m] / count_sum[m] for m in price_sum}
        top3 = sorted(counts.items(), key=lambda x: (-x[1], -avg[x[0]]))[:3]
        idx_map = {}
        for ln in open(self.root / "models_index.txt", 'r', encoding='utf-8'):
            k, n = ln.strip().split(';')
            idx_map[int(k)] = int(n)
        mlines = open(
            self.root / "models.txt", 'r', encoding='utf-8'
            ).readlines()
        result = []
        for m, cnt in top3:
            parts = mlines[idx_map[m]].rstrip("\n").split(';')
            name, brand = parts[1].strip(), parts[2].strip()
            result.append(ModelSaleStats(car_model_name=name,
                                         brand=brand,
                                         sales_number=cnt))
        return result
