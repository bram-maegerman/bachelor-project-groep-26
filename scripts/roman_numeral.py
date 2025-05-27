import re

class RomanNumeral:

    def __init__(self, val):
        if isinstance(val, str):
            if not self.is_valid_roman(val):
                raise ValueError(f"Invalid Roman numeral format: {val}")
            self.__representation = val
            self.__decimal_val = self.__calculate(val)

        elif isinstance(val, int):
            self.__decimal_val = val
            self.__representation = self.__convert_to_roman(val)
        else:
            raise TypeError(f"Unsupported type for RomanNumeral: {type(val)}")


    def __roman_regex(self):
        return re.compile(
        r"^M{0,3}(CM|CD|D?C{0,3})"
        r"(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$",
        re.IGNORECASE
        )

    def is_valid_roman(self, s):
        return bool(self.__roman_regex().fullmatch(s))

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

    def __convert_to_roman(self, decimal_val):
        if decimal_val < 1 or decimal_val > 3999:
            raise ValueError(f"Decimal value out of range (1-3999): {decimal_val}")

        roman_numerals = [
            ("m", 1000),
            ("cm", 900),
            ("d", 500),
            ("cd", 400),
            ("c", 100),
            ("xc", 90),
            ("l", 50),
            ("xl", 40),
            ("x", 10),
            ("ix", 9),
            ("v", 5),
            ("iv", 4),
            ("i", 1)
        ]

        result = ""
        for numeral, value in roman_numerals:
            while decimal_val >= value:
                result += numeral
                decimal_val -= value

        return result

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

    def __eq__(self, other):
        if isinstance(other, RomanNumeral):
            return self.__decimal_val == other.__decimal_val
        elif isinstance(other, int):
            return self.__decimal_val == other
        else:
            return NotImplemented

    # function to add decimal value to the roman numeral
    def __add__(self, other):
        if isinstance(other, RomanNumeral):
            return self.__decimal_val + other.__decimal_val
        elif isinstance(other, int):
            return self.__decimal_val + other
        else:
            return NotImplemented

    # function to subtract decimal value from the roman numeral
    def __sub__(self, other):
        if isinstance(other, RomanNumeral):
            return self.__decimal_val - other.__decimal_val
        elif isinstance(other, int):
            return self.__decimal_val - other
        else:
            return NotImplemented

    def __int__(self):
        return int(self.__decimal_val)

    def __hash__(self):
        return hash(int(self))

    def __repr__(self):
        return str(self.__representation)

    @property
    def roman_representation(self):
        return self.__representation.upper()

    @property
    def decimal_value(self):
        return self.__decimal_val