import pandas as pd
import re
from JLError import JLError
from typing import Union


class FileHandler:
    """
    Class responsible for files manipulations e.g. extracting data, merging files, creating new csv file as a result.
    """

    @classmethod
    def _check_file_extension(cls, file: str) -> Union[str | JLError]:
        """
        Verifies if file extension is in supported formats.
        :param file: Path to the file.
        :return: file extension or JLError
        """
        supported_file_types = {"xls", "xlsx", "csv"}
        file_extension = file.split(".")[-1]

        if file_extension in supported_file_types:
            return file_extension
        else:
            error = JLError("Unsupported file type.\n"
                            "Please use only excel or csv files.")
            return error

    @classmethod
    def _load_data(cls, file: str) -> Union[pd.DataFrame | JLError]:
        """
        Loads data from file into pandas DataFrame
        :param file: Path to the file.
        :return: pandas DataFrame with loaded data from file or JLError
        """
        supported_methods = {"xls": pd.read_excel,
                             "xlsx": pd.read_excel,
                             "csv": pd.read_csv}

        file_type_check_result = cls._check_file_extension(file)

        if isinstance(file_type_check_result, JLError):
            return file_type_check_result

        try:
            raw_data = supported_methods[file_type_check_result](file)
        except FileNotFoundError:
            error = JLError("File not found!")
            return error
        else:
            return raw_data

    @classmethod
    def _determine_current_pi(cls, sprints: list) -> str:
        """
        Finds which is current pi.
        :param sprints: List of sprints extracted from Jira.
        :return: Current pi.
        """
        pattern = r'[0-9]{2}\.[0-9]{1}'
        result = max([(re.search(pattern, pi).group(0)) for pi in sprints])
        return result

    @classmethod
    def _determine_latest_sprint(cls, sprints: list, current_pi: str) -> str:
        """
        Finds which is current sprint.
        :param sprints: List of sprints extracted from Jira.
        :param current_pi: Name of current pi.
        :return: Current sprint.
        """
        result = max([sprint[-1] for sprint in sprints if str(current_pi) in sprint])
        return result

    @classmethod
    def _compose_query(cls, sprints: list, current_pi: str, current_sprint: str) -> str:
        """
        Creates query of sprint with current pi and current sprint.
        :param sprints: List of sprints extracted from Jira.
        :return: Query of sprint with current pi and current sprint.
        """

        # We extract following data as example: 'Team Kiwi PI23.1 Sprint 5'
        raw_data = sprints[0]
        # This pattern will match '23.1' from above
        pi_pattern = r'[0-9]{2}\.[0-9]{1}'
        # This pattern will match '5' from example above (the last digit in the string).
        sprint_pattern = r'[0-9]{1}$'
        # Below we replace '23.1' with latest pi number.
        modified_query = re.sub(pi_pattern, current_pi, raw_data)
        # Below we replace sprint number with latest sprint number.
        final_query = re.sub(sprint_pattern, current_sprint, modified_query)

        return final_query

    @classmethod
    def _normalize_jira_export_file(cls, file: str) -> Union[pd.DataFrame | JLError]:
        """
        Normalizes data in pandas DataFrame, by filtering unnecessary information extracted from Jira export.
        :param file: Path to Jira extraction file.
        :return: Normalized Pandas DataFrame or JLError
        """
        file_extraction_result = cls._load_data(file)

        if isinstance(file_extraction_result, JLError):
            return file_extraction_result

        try:
            # Truncating table to contain only columns we need
            truncated_data = file_extraction_result[["Summary", "Issue key", "Issue Type",
                                                     "Custom field (Feature Link)", "Sprint"]]

        except KeyError:
            error = JLError("One or more table columns missing.\n"
                            "Please check if table is in expected format.")
            return error

        # Replacing column name from "Custom field (Feature Link)" to "Feature"
        truncated_data = truncated_data.rename(columns={"Custom field (Feature Link)": "Feature"})
        # Sorting "Issue Type" column to show only "Story" rows
        truncated_data = truncated_data.query("`Issue Type` == 'Story'")
        # Getting information of items in "Sprint" column
        sprints_info = truncated_data.loc[:, "Sprint"]
        # Finding which is current PI
        active_pi = cls._determine_current_pi(sprints_info)
        # Finding which is the latest sprint number
        active_sprint = cls._determine_latest_sprint(sprints_info, active_pi)
        # Setting sorting criteria to show us only features from latest sprint
        query = cls._compose_query(sprints_info, active_pi, active_sprint)
        normalized_data = truncated_data.query("Sprint == @query")
        # print(normalized_data)
        return normalized_data

    @classmethod
    def _normalize_map_file(cls, file: str) -> Union[pd.DataFrame | JLError]:
        """
        Normalizes data in pandas DataFrame, by filtering unnecessary information extracted from Mapping file.
        :param file: Path to the mapping file.
        :return: Normalized Pandas DataFrame or JLError.
        """
        file_extraction_result = cls._load_data(file)

        if isinstance(file_extraction_result, JLError):
            return file_extraction_result

        try:
            # Truncating table to contain only columns we need
            normalized_map_data = file_extraction_result[["Feature", "Label"]]
        except KeyError:
            error = JLError("One or more table columns missing.\n"
                            "Please check if table is in expected format.")
            return error

        return normalized_map_data

    @classmethod
    def _merge_files(cls, file: Union[pd.DataFrame | JLError], map_file: Union[pd.DataFrame | JLError]) -> Union[pd.DataFrame | JLError]:
        """
        Merges both Pandas DataFrames from Jira extraction and mapping file.
        :param file: Path to Jira extraction file.
        :param map_file: Path to the mapping file.
        :return: Merged Pandas DataFrame of JLError.
        """
        normalized_jira_output_result = cls._normalize_jira_export_file(file)
        normalized_map_file_result = cls._normalize_map_file(map_file)
        error = None
        if isinstance(normalized_jira_output_result, JLError) and isinstance(normalized_map_file_result, JLError):
            error = JLError(f"{normalized_jira_output_result}(from Jira extraction file) and\n"
                            f"{normalized_map_file_result} (from map file)")
        elif isinstance(normalized_jira_output_result, JLError):
            error = JLError(f"{normalized_jira_output_result} (from Jira extraction file)")
        elif isinstance(normalized_map_file_result, JLError):
            error = JLError(f"{normalized_map_file_result} (from map file)")
        if error:
            return error
        # Merge both Dataframes on "Feature" column
        merged_data = pd.merge(normalized_jira_output_result, normalized_map_file_result, on=["Feature"])
        # Merge "Issue key" and "Summary" columns information to one column named "Summary"
        merged_data["Summary"] = merged_data[["Issue key", "Summary"]].apply(" ".join, axis=1)

        return merged_data

    @classmethod
    def generate_csv(cls, jira_file: Union[pd.DataFrame | JLError], map_file: Union[pd.DataFrame | JLError],
                     export_file_name: str) -> Union[pd.DataFrame | str]:
        """
        Generates csv file based on normalized and merged Pandas DataFrames from Jira extraction and mapping file.
        :param jira_file: Path to Jira extraction file.
        :param map_file: Path to the mapping file.
        :param export_file_name: Name of csv file to be generated.
        :return: Information that process finished successfully or JLError.
        """
        table_to_export_result = cls._merge_files(jira_file, map_file)
        export_file_name += ".csv"
        if isinstance(table_to_export_result, JLError):
            return table_to_export_result.message
        else:
            table_to_export_result.to_csv(export_file_name, columns=["Issue Type", "Summary", "Label"], index=False)
            return "CSV file generated successfully!"
