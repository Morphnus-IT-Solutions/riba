
def normalize_phone(phone):
    cleaned = ''
    
    # if the input field has seperators, we read data till first seperator
    separators = ',/'
    for seperator in separators:
        phone = phone[:phone.index(seperator)]

    for char in phone:
        if char in ['0123456789']:
            cleaned += char

    if len(cleaned) == 12 and cleaned[:2] == '91':
        # phone is prefixed with country code, remove it
        return cleaned[2:]
    if len(cleaned) == 11 and cleaned[:1] == '0':
        # phone is prefixed with zero, remove it
        return cleaned[1:]

    if len(cleaned) == 13 and cleaned[:3] == '091':
        # phone is prefixed with zero and country code
        return cleaned[3:]

    return cleaned
