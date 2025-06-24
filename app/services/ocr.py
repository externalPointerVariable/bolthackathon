import requests
import json
from dataclasses import dataclass, asdict, fields
from config.config import azure_ocr_endpoint, azure_ocr_access_key
from typing import List, Any, get_args

@dataclass
class Metadata:
    width: int
    height: int

@dataclass
class BoundingPolygon:
    x: int
    y: int

@dataclass
class Word:
    text: str
    boundingPolygon: List[BoundingPolygon]
    confidence: float

@dataclass
class Line:
    text: str
    boundingPolygon: List[BoundingPolygon]
    words: List[Word]

@dataclass
class Block:
    lines: List[Line]

@dataclass
class ReadResult:
    blocks: List[Block]

@dataclass
class AnalyzeResult:
    modelVersion: str
    metadata: Metadata
    readResult: ReadResult

@dataclass
class AnalyzeRequest:
    uri: str

class OCR:
    def from_dict(self, data_class: Any, data: Any):
        if isinstance(data, list):
            args = get_args(data_class)
            if args:
                return [self.from_dict(args[0], item) for item in data]
            return data

        if isinstance(data, dict):
            fieldtypes = {f.name: f.type for f in fields(data_class)}
            return data_class(**{
                k: self.from_dict(fieldtypes[k], v) if k in fieldtypes else v
                for k, v in data.items()
            })

        return data

    def recognize_text(self, public_image_url: str = None):
        endpoint = azure_ocr_endpoint
        url = f"{endpoint}computervision/imageanalysis:analyze?features=read&api-version=2023-10-01"
        key = azure_ocr_access_key
        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Content-Type': 'application/json'
        }

        image_url = public_image_url
        request_payload = AnalyzeRequest(uri=image_url)
        response = requests.post(url, headers=headers, json=asdict(request_payload))

        try:
            data = response.json()
            result = self.from_dict(AnalyzeResult, data)
            final_result = ""
            for block in result.readResult.blocks:
                for line in block.lines:
                    final_result += line.text + "/n"
            return final_result        

        except Exception as e:
            print(f"Deserialization error: {e}")

if __name__ == "__main__":
    OCR().recognize_text()