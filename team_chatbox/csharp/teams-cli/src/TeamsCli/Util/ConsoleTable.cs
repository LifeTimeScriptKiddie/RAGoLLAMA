using System.Text;

namespace TeamsCli.Util;

public class ConsoleTable
{
    private readonly List<string> _headers;
    private readonly List<List<string>> _rows = new();

    public ConsoleTable(params string[] headers)
    {
        _headers = headers.ToList();
    }

    public void AddRow(params string[] values)
    {
        if (values.Length != _headers.Count)
            throw new ArgumentException($"Row must have {_headers.Count} values");

        _rows.Add(values.ToList());
    }

    public void Print()
    {
        var columnWidths = CalculateColumnWidths();
        
        PrintSeparator(columnWidths);
        PrintRow(_headers, columnWidths);
        PrintSeparator(columnWidths);
        
        foreach (var row in _rows)
        {
            PrintRow(row, columnWidths);
        }
        
        PrintSeparator(columnWidths);
    }

    private List<int> CalculateColumnWidths()
    {
        var widths = _headers.Select(h => h.Length).ToList();
        
        foreach (var row in _rows)
        {
            for (int i = 0; i < row.Count; i++)
            {
                widths[i] = Math.Max(widths[i], row[i]?.Length ?? 0);
            }
        }

        return widths;
    }

    private void PrintSeparator(List<int> columnWidths)
    {
        var separator = new StringBuilder("+");
        
        foreach (var width in columnWidths)
        {
            separator.Append(new string('-', width + 2));
            separator.Append("+");
        }
        
        Console.WriteLine(separator.ToString());
    }

    private void PrintRow(List<string> values, List<int> columnWidths)
    {
        var row = new StringBuilder("|");
        
        for (int i = 0; i < values.Count; i++)
        {
            var value = values[i] ?? "";
            row.Append($" {value.PadRight(columnWidths[i])} |");
        }
        
        Console.WriteLine(row.ToString());
    }
}