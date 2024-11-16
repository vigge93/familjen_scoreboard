def str_length_validator(min=0, max=255):
    def validate(value):
        length = len(value)
        if min <= length <= max:
            return value
        raise ValueError(f"String must have a length between {min} and {max}")

    return validate
