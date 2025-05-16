class RomanNumeral:

    def __init__(self, val):
        self.__representation = val.lower()
        self.__decimal_val = self.__calculate(self.__representation)

    ##calculate decimal value of a roman numeral string
    def __calculate(self, value):
        if not value:
            return 0

        if len(value) == 1:
            return self.__get_decimal_value(value[0])

        current_val = self.__get_decimal_value(value[0])
        next_val = self.__get_decimal_value(value[1])

        if current_val < next_val:
            return next_val - current_val + self.__calculate(value[2:])
        else:
            return current_val + self.__calculate(value[1:])

    ##Convert a single Roman numeral character to its decimal value.
    def __get_decimal_value(self, roman_numeral):

        representation_dict = {
            "m": 1000,
            "d": 500,
            "c": 100,
            "l": 50,
            "x": 10,
            "v": 5,
            "i": 1
        }

        try:
            return representation_dict[roman_numeral.lower()]
        except KeyError:
            raise ValueError(f"Invalid Roman numeral character: {roman_numeral}")

    def get_decimal(self):
        return self.__decimal_val

    def __lt__(self, other):
        if isinstance(other, RomanNumeral):
            return self.__decimal_val < other.__decimal_val
        elif isinstance(other, int):
            return self.__decimal_val < other
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, RomanNumeral):
            return self.__decimal_val <= other.__decimal_val
        elif isinstance(other, int):
            return self.__decimal_val <= other
        else:
            return NotImplemented

    def  __gt__(self, other):
        if isinstance(other, RomanNumeral):
            return self.__decimal_val > other.__decimal_val
        elif isinstance(other, int):
            return self.__decimal_val > other
        else:
            return NotImplemented

    def  __ge__(self, other):
        if isinstance(other, RomanNumeral):
            return self.__decimal_val >= other.__decimal_val
        elif isinstance(other, int):
            return self.__decimal_val >= other
        else:
            return NotImplemented

    @property
    def roman_representation(self):
        return self.__representation.upper()

    @property
    def decimal_value(self):
        return self.__decimal_val

    def __repr__(self):
        return self.roman_representation