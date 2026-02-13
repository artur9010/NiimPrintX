import aiohttp
from typing import Optional, Dict, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class CloudLabelInfo:
    barcode: str
    width_mm: int
    height_mm: int
    name: str
    name_en: str
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'CloudLabelInfo':
        label_data = data.get('data', {})
        
        name_en = ""
        for name_item in label_data.get('names', []):
            if name_item.get('languageCode') == 'en':
                name_en = name_item.get('name', '')
                break
        
        return cls(
            barcode=label_data.get('barcode', ''),
            width_mm=label_data.get('width', 0),
            height_mm=label_data.get('height', 0),
            name=label_data.get('name', ''),
            name_en=name_en
        )


class NiimbotCloudService:
    API_BASE = "https://print.niimbot.com/api"
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "niimbot-user-agent": "AppVersionName/999.0.0"
                }
            )
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_label_by_barcode(self, barcode: str) -> Optional[CloudLabelInfo]:
        url = f"{self.API_BASE}/template/getCloudTemplateByOneCode"
        
        try:
            session = await self._get_session()
            async with session.post(url, json={"oneCode": barcode}) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('code') == 1:
                        logger.info(f"Cloud label info for {barcode}: {data.get('data', {}).get('name', 'unknown')}")
                        return CloudLabelInfo.from_api_response(data)
                    else:
                        logger.warning(f"Cloud API error for {barcode}: {data.get('message', 'unknown error')}")
                else:
                    logger.warning(f"Cloud API HTTP error: {response.status}")
        except Exception as e:
            logger.error(f"Failed to fetch label info from cloud: {e}")
        
        return None
    
    async def get_rfid_info(self, serial_number: str) -> Optional[Dict[str, Any]]:
        url = f"{self.API_BASE}/rfid/getRfid"
        
        try:
            session = await self._get_session()
            async with session.post(url, json={"serialNumber": serial_number}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
        except Exception as e:
            logger.error(f"Failed to fetch RFID info: {e}")
        
        return None
