
import asyncio
import json

from app.llm.async_service import benchmark_async_execution


QUESTIONS = [
    "What is Python?",
    "Explain object-oriented programming.",
    "What is an API?",
    "Explain REST API.",
    "What is asynchronous programming?",
    "Explain machine learning.",
    "What is a neural network?",
    "Explain database indexing.",
    "What is a Python decorator?",
    "Explain the difference between HTTP and HTTPS.",
]


async def main():
    print("=" * 60)
    print("ASYNC LLM PERFORMANCE BENCHMARK")
    print("=" * 60)

    print(f"\nTotal questions: {len(QUESTIONS)}")
    print("Model: Local Ollama model from project configuration")
    print("Maximum concurrent requests: 3")

    benchmark = await benchmark_async_execution(
        QUESTIONS,
        max_concurrency=3,
    )

    sequential = benchmark["sequential"]
    concurrent = benchmark["concurrent"]

    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)

    print("\nSEQUENTIAL EXECUTION")
    print(f"Total questions: {sequential['total_questions']}")
    print(f"Successful: {sequential['successful_requests']}")
    print(f"Failed: {sequential['failed_requests']}")
    print(f"Time: {sequential['elapsed_seconds']} seconds")

    print("\nCONCURRENT EXECUTION")
    print(f"Total questions: {concurrent['total_questions']}")
    print(f"Successful: {concurrent['successful_requests']}")
    print(f"Failed: {concurrent['failed_requests']}")
    print(f"Time: {concurrent['elapsed_seconds']} seconds")

    print("\nPERFORMANCE COMPARISON")
    print(f"Speedup: {benchmark['speedup']}x")

    print("\nCONCURRENT REQUEST DETAILS")

    for index, result in enumerate(
        concurrent["results"],
        start=1,
    ):
        status = "SUCCESS" if result["success"] else "FAILED"

        print(f"\nQuestion {index}: {result['prompt']}")
        print(f"Status: {status}")

        if result["success"]:
            print(f"Answer: {result['answer'][:150]}")
        else:
            print(f"Error: {result['error']}")

    with open(
        "async_benchmark_results.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(benchmark, file, indent=4)

    print("\nResults saved to async_benchmark_results.json")


if __name__ == "__main__":
    asyncio.run(main())
