"""
Script to generate all timezones with their UTC offsets
"""
import pytz
from datetime import datetime

def generate_timezones():
    """Generate all timezones with UTC offsets"""
    all_zones = pytz.all_timezones
    
    zones_data = []
    for tz_name in all_zones:
        try:
            tz = pytz.timezone(tz_name)
            now = datetime.now(tz)
            offset = now.strftime('%z')
            
            # تبدیل +0330 به +03:30
            if len(offset) == 5:
                offset_formatted = f'{offset[:3]}:{offset[3:]}'
            else:
                offset_formatted = '+00:00'
            
            # نام نمایشی
            display_name = f"{tz_name.replace('_', ' ')} (UTC{offset_formatted})"
            
            zones_data.append({
                'code': tz_name,
                'name': tz_name.split('/')[-1].replace('_', ' '),
                'utc_offset': offset_formatted,
                'display_name': display_name,
                'is_default': tz_name == 'Asia/Tehran',
                'is_active': True,
                'order': 0 if tz_name == 'Asia/Tehran' else 999
            })
        except:
            pass
    
    # مرتب‌سازی بر اساس offset
    zones_data.sort(key=lambda x: (x['utc_offset'], x['code']))
    
    # تنظیم order
    for i, zone in enumerate(zones_data):
        if zone['code'] != 'Asia/Tehran':
            zone['order'] = i + 1
    
    return zones_data

if __name__ == '__main__':
    zones = generate_timezones()
    print(f"Total timezones: {len(zones)}")
    
    # چاپ به فرمت Python dict
    print("\ntimezones = [")
    for zone in zones:
        print(f"    {zone},")
    print("]")
