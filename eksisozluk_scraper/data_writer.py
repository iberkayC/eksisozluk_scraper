"""
Module to write data to files in either CSV or JSON format.

Raises:
    ValueError: if an unsupported format is specified.
"""
import csv
import json
from typing import List, Dict, Any, Literal


class DataWriter:
    """
    Class to write data to files in either CSV or JSON format.

    Raises:
        ValueError: if an unsupported format is specified.
    """
    @staticmethod
    def write_data(filename: str,
                   data: List[Dict[str, Any]],
                   filetype: Literal['csv', 'json']) -> None:
        """
        Write data to a file in either CSV or JSON format.

        Args:
            filename (str): the name of the file to write.
            data (List[Dict[str, Any]]): the data to write.
            filetype (Literal['csv', 'json']): the output format ('csv' or 'json').

        Raises:
            ValueError: if an unsupported format is specified.
        """
        if filetype == 'csv':
            DataWriter._write_csv(filename, data)
        elif filetype == 'json':
            DataWriter._write_json(filename, data)
        else:
            raise ValueError(f"Unsupported format: {filetype}")

    @staticmethod
    def _write_csv(filename: str, data: List[Dict[str, Any]]) -> None:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            if not data:
                return
            fieldnames = data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    @staticmethod
    def _write_json(filename: str, data: List[Dict[str, Any]]) -> None:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
