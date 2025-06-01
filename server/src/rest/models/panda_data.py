from enum import Enum
from typing import NamedTuple
from pydantic import BaseModel


class DefectInfo(NamedTuple):
    color: tuple[int, int, int]
    defect: str


class DefectType(Enum):
    POR = DefectInfo((255, 50, 50), 'пора')
    VKL = DefectInfo((0, 255, 0), 'включение')
    PODREZ = DefectInfo((0, 0, 255), 'подрез')
    PROZHOG = DefectInfo((255, 255, 0), 'прожог')
    TRESCHINA = DefectInfo((255, 0, 255), 'трещина')
    NAPLIV = DefectInfo((0, 255, 255), 'наплыв')
    ETALON1 = DefectInfo((255, 64, 64), 'эталон1')
    ETALON2 = DefectInfo((64, 255, 64), 'эталон2')
    ETALON3 = DefectInfo((0, 0, 128), 'эталон3')
    HIDDEN_POR = DefectInfo((128, 128, 0), 'пора-скрытая')
    UTJAZHINA = DefectInfo((128, 0, 128), 'утяжина')
    NESPLAVLENIE = DefectInfo((0, 128, 128), 'несплавление')
    NEPROVAR = DefectInfo((192, 192, 192), 'непровар корня')

    @property
    def color(self):
        return self.value.color

    @property
    def defect(self):
        return self.value.defect

    @classmethod
    def get_by_id(cls, class_id: int) -> 'DefectType':
        """Получение DefectType по числовому ID (0, 1, 2...)"""
        try:
            return list(cls)[class_id]
        except IndexError:
            raise ValueError(f"Invalid defect class ID: {class_id}")

    @classmethod
    def get_defect_info(cls, class_id: int) -> DefectInfo:
        """Получение DefectInfo по числовому ID"""
        return cls.get_by_id(class_id).value


class DefectItem(BaseModel):
    type: DefectType
    count: int


class LabelData(BaseModel):
    s3_txt_path: str
    label: str
