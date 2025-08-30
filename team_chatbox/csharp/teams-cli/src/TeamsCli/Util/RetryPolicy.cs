using System.Net;

namespace TeamsCli.Util;

public class RetryPolicy
{
    private const int MaxRetries = 5;
    private static readonly Random Random = new();

    public static async Task<T> ExecuteAsync<T>(Func<Task<T>> operation)
    {
        var attempt = 0;
        Exception? lastException = null;

        while (attempt < MaxRetries)
        {
            try
            {
                return await operation();
            }
            catch (HttpRequestException ex) when (ex.Message.Contains("429") || ex.Message.Contains("5"))
            {
                lastException = ex;
                attempt++;

                if (attempt >= MaxRetries)
                    break;

                var delay = CalculateDelay(attempt, ex.Message.Contains("429"));
                await Task.Delay(delay);
            }
            catch (Exception ex)
            {
                throw;
            }
        }

        throw new InvalidOperationException($"Operation failed after {MaxRetries} attempts", lastException);
    }

    private static TimeSpan CalculateDelay(int attempt, bool isRateLimit)
    {
        if (isRateLimit)
        {
            return TimeSpan.FromSeconds(60);
        }

        var baseDelay = Math.Pow(2, attempt) * 1000;
        var jitter = Random.Next(0, 1000);
        return TimeSpan.FromMilliseconds(baseDelay + jitter);
    }
}