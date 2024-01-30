"""
Contains the CSVWriter class, which is used to write data to csv files.
"""
import csv
import aiofiles


class CSVWriter:
    """
    Class to write data to csv files.
    """
    @staticmethod
    async def write_to_csv(filename: str,
                           data: list) -> None:
        """Asynchronous data writing to csv file.

        Args:
            filename (str): the name of the file to write.
            data (list): the data to write.
        """
        async with aiofiles.open(filename, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['Content', 'Author', 'Date Created', 'Last Changed']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            await writer.writeheader()
            for row in data:
                await writer.writerow(row)
