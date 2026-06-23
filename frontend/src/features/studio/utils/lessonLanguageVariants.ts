import type { ExecutionLanguage } from '../../../types/execution';
import type { LearningLesson } from '../../../types/learning';

type LessonStage = 'learn' | 'implement';

interface CodeVariant {
  learn: string;
  implement: string;
}

export function resolveLessonCode(
  lesson: LearningLesson,
  stage: LessonStage,
  language: ExecutionLanguage,
): string {
  if (language === lesson.language) {
    return stage === 'implement'
      ? lesson.implementationChallenge.starterCode
      : lesson.learningContent.walkthroughCode;
  }
  if (language === 'python') {
    return stage === 'implement'
      ? lesson.implementationChallenge.starterCode
      : lesson.learningContent.walkthroughCode;
  }

  const lessonVariant = buildVariantForLesson(lesson.id, language);
  if (lessonVariant) {
    return stage === 'implement' ? lessonVariant.implement : lessonVariant.learn;
  }

  const variant = buildVariantForMode(lesson.visualizationMode, language);
  return stage === 'implement' ? variant.implement : variant.learn;
}

function buildVariantForLesson(
  lessonId: string,
  language: Exclude<ExecutionLanguage, 'python'>,
): CodeVariant | null {
  const variants: Record<string, (() => CodeVariant) | null> = {
    'lesson-variable-flow': language === 'c' ? cScalarVariant : javaScalarVariant,
    'lesson-comparison-if': language === 'c' ? cComparisonIfVariant : javaComparisonIfVariant,
    'lesson-if-else-branch': language === 'c' ? cIfElseVariant : javaIfElseVariant,
    'lesson-logical-operators': language === 'c' ? cLogicalOperatorsVariant : javaLogicalOperatorsVariant,
    'lesson-for-loop-sum': language === 'c' ? cForLoopSumVariant : javaForLoopSumVariant,
    'lesson-while-loop-counter': language === 'c' ? cWhileLoopCounterVariant : javaWhileLoopCounterVariant,
    'lesson-nested-loops': language === 'c' ? cNestedLoopsVariant : javaNestedLoopsVariant,
    'lesson-list-indexing': language === 'c' ? cArrayCellsVariant : javaArrayCellsVariant,
    'lesson-function-return': language === 'c' ? cFunctionReturnVariant : javaFunctionReturnVariant,
    'lesson-lambda-functions': language === 'java' ? javaLambdaFunctionsVariant : null,
    'lesson-input-parsing': language === 'c' ? cInputParsingVariant : javaInputParsingVariant,
    'lesson-linear-search': language === 'c' ? cLinearSearchVariant : javaLinearSearchVariant,
    'lesson-array-cells': language === 'c' ? cArrayCellsVariant : javaArrayCellsVariant,
    'lesson-hash-map-counting': language === 'c' ? cHashMapCountingVariant : javaHashMapCountingVariant,
    'lesson-deque-both-ends': language === 'c' ? cDequeVariant : javaDequeVariant,
    'lesson-merge-sort': language === 'java' ? javaMergeSortShowcaseVariant : cArraySortVariant,
    'lesson-radix-sort': language === 'c' ? cRadixSortShowcaseVariant : javaArraySortVariant,
  };

  const variantBuilder = variants[lessonId];
  return variantBuilder ? variantBuilder() : null;
}

function buildVariantForMode(mode: string, language: Exclude<ExecutionLanguage, 'python'>): CodeVariant {
  const normalizedMode = mode.toLowerCase();

  if (normalizedMode.includes('binary') || normalizedMode.includes('bound')) {
    return language === 'c' ? cBinarySearchVariant() : javaBinarySearchVariant();
  }
  if (normalizedMode.includes('two-pointers')) {
    return language === 'c' ? cTwoPointersVariant() : javaTwoPointersVariant();
  }
  if (normalizedMode.includes('sliding-window')) {
    return language === 'c' ? cSlidingWindowVariant() : javaSlidingWindowVariant();
  }
  if (normalizedMode.includes('prefix-sum')) {
    return language === 'c' ? cPrefixSumVariant() : javaPrefixSumVariant();
  }
  if (normalizedMode.includes('palindrome')) {
    return language === 'c' ? cPalindromeVariant() : javaPalindromeVariant();
  }
  if (normalizedMode.includes('stack')) {
    return language === 'c' ? cStackVariant() : javaStackVariant();
  }
  if (normalizedMode.includes('queue') || normalizedMode.includes('deque')) {
    return language === 'c' ? cQueueVariant() : javaQueueVariant();
  }
  if (
    normalizedMode.includes('recursion')
    || normalizedMode.includes('backtracking')
    || normalizedMode.includes('divide-and-conquer')
    || normalizedMode.includes('memoized')
    || normalizedMode.includes('call-stack')
  ) {
    return language === 'c' ? cRecursionVariant() : javaRecursionVariant();
  }
  if (
    normalizedMode.includes('dp')
    || normalizedMode.includes('knapsack')
    || normalizedMode.includes('lcs')
    || normalizedMode.includes('edit-distance')
    || normalizedMode.includes('grid')
  ) {
    return language === 'c' ? cDpVariant() : javaDpVariant();
  }
  if (normalizedMode.includes('tree')) {
    return language === 'c' ? cTreeVariant() : javaTreeVariant();
  }
  if (normalizedMode.includes('graph') || normalizedMode.includes('dijkstra')) {
    return language === 'c' ? cGraphVariant() : javaGraphVariant();
  }
  if (
    normalizedMode.includes('selection')
    || normalizedMode.includes('bubble')
    || normalizedMode.includes('insertion')
    || normalizedMode.includes('merge')
    || normalizedMode.includes('quick')
    || normalizedMode.includes('heap')
    || normalizedMode.includes('shell')
    || normalizedMode.includes('radix')
    || normalizedMode.includes('array-bars')
  ) {
    return language === 'c' ? cArraySortVariant() : javaArraySortVariant();
  }
  if (normalizedMode.includes('array-cells') || normalizedMode.includes('array')) {
    return language === 'c' ? cArrayCellsVariant() : javaArrayCellsVariant();
  }

  return language === 'c' ? cScalarVariant() : javaScalarVariant();
}

function cScalarVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int value = 2;
    value = value + 5;
    value = value * 2;
    printf("%d\\n", value);
    return 0;
}
`,
    implement: `#include <stdio.h>

int transform_value(int value) {
    /* TODO: add 5, then multiply by 2. */
    return value;
}

int main(void) {
    printf("%d\\n", transform_value(2));
    return 0;
}
`,
  };
}

function javaScalarVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        int value = 2;
        value = value + 5;
        value = value * 2;
        System.out.println(value);
    }
}
`,
    implement: `public class Main {
    static int transformValue(int value) {
        // TODO: add 5, then multiply by 2.
        return value;
    }

    public static void main(String[] args) {
        System.out.println(transformValue(2));
    }
}
`,
  };
}

function cComparisonIfVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int score = 75;
    if (score >= 60) {
        printf("pass\\n");
    }
    return 0;
}
`,
    implement: `#include <stdio.h>

int is_pass(int score) {
    /* TODO: return 1 when score is at least 60. */
    return 0;
}

int main(void) {
    printf("%d\\n", is_pass(75));
    return 0;
}
`,
  };
}

function javaComparisonIfVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        int score = 75;
        if (score >= 60) {
            System.out.println("pass");
        }
    }
}
`,
    implement: `public class Main {
    static boolean isPass(int score) {
        // TODO: return true when score is at least 60.
        return false;
    }

    public static void main(String[] args) {
        System.out.println(isPass(75));
    }
}
`,
  };
}

function cIfElseVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int number = 7;
    if (number % 2 == 0) {
        printf("even\\n");
    } else {
        printf("odd\\n");
    }
    return 0;
}
`,
    implement: `#include <stdio.h>

const char *parity_label(int number) {
    /* TODO: return "even" or "odd". */
    return "";
}

int main(void) {
    printf("%s\\n", parity_label(7));
    return 0;
}
`,
  };
}

function javaIfElseVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        int number = 7;
        if (number % 2 == 0) {
            System.out.println("even");
        } else {
            System.out.println("odd");
        }
    }
}
`,
    implement: `public class Main {
    static String parityLabel(int number) {
        // TODO: return "even" or "odd".
        return "";
    }

    public static void main(String[] args) {
        System.out.println(parityLabel(7));
    }
}
`,
  };
}

function cLogicalOperatorsVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>
#include <stdbool.h>

int main(void) {
    int age = 17;
    bool has_card = true;
    bool can_enter = age >= 18 || has_card;
    printf("%s\\n", can_enter ? "true" : "false");
    return 0;
}
`,
    implement: `#include <stdio.h>
#include <stdbool.h>

bool can_enter(int age, bool has_card) {
    /* TODO: use || to allow adults or card holders. */
    return false;
}

int main(void) {
    printf("%s\\n", can_enter(17, true) ? "true" : "false");
    return 0;
}
`,
  };
}

function javaLogicalOperatorsVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        int age = 17;
        boolean hasCard = true;
        boolean canEnter = age >= 18 || hasCard;
        System.out.println(canEnter);
    }
}
`,
    implement: `public class Main {
    static boolean canEnter(int age, boolean hasCard) {
        // TODO: use || to allow adults or card holders.
        return false;
    }

    public static void main(String[] args) {
        System.out.println(canEnter(17, true));
    }
}
`,
  };
}

function cForLoopSumVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int total = 0;
    for (int i = 1; i <= 5; i++) {
        total += i;
    }
    printf("%d\\n", total);
    return 0;
}
`,
    implement: `#include <stdio.h>

int sum_to_n(int n) {
    int total = 0;
    /* TODO: add numbers from 1 to n. */
    return total;
}

int main(void) {
    printf("%d\\n", sum_to_n(5));
    return 0;
}
`,
  };
}

function javaForLoopSumVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        int total = 0;
        for (int i = 1; i <= 5; i++) {
            total += i;
        }
        System.out.println(total);
    }
}
`,
    implement: `public class Main {
    static int sumToN(int n) {
        int total = 0;
        // TODO: add numbers from 1 to n.
        return total;
    }

    public static void main(String[] args) {
        System.out.println(sumToN(5));
    }
}
`,
  };
}

function cWhileLoopCounterVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int count = 3;
    while (count > 0) {
        printf("%d\\n", count);
        count--;
    }
    return 0;
}
`,
    implement: `#include <stdio.h>

int count_down_sum(int start) {
    int total = 0;
    /* TODO: add values while counting down to 1. */
    return total;
}

int main(void) {
    printf("%d\\n", count_down_sum(3));
    return 0;
}
`,
  };
}

function javaWhileLoopCounterVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        int count = 3;
        while (count > 0) {
            System.out.println(count);
            count--;
        }
    }
}
`,
    implement: `public class Main {
    static int countDownSum(int start) {
        int total = 0;
        // TODO: add values while counting down to 1.
        return total;
    }

    public static void main(String[] args) {
        System.out.println(countDownSum(3));
    }
}
`,
  };
}

function cNestedLoopsVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int count = 0;
    for (int row = 1; row <= 2; row++) {
        for (int col = 1; col <= 3; col++) {
            count++;
        }
    }
    printf("%d\\n", count);
    return 0;
}
`,
    implement: `#include <stdio.h>

int grid_cell_count(int rows, int cols) {
    int count = 0;
    /* TODO: count every row and column pair. */
    return count;
}

int main(void) {
    printf("%d\\n", grid_cell_count(2, 3));
    return 0;
}
`,
  };
}

function javaNestedLoopsVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        int count = 0;
        for (int row = 1; row <= 2; row++) {
            for (int col = 1; col <= 3; col++) {
                count++;
            }
        }
        System.out.println(count);
    }
}
`,
    implement: `public class Main {
    static int gridCellCount(int rows, int cols) {
        int count = 0;
        // TODO: count every row and column pair.
        return count;
    }

    public static void main(String[] args) {
        System.out.println(gridCellCount(2, 3));
    }
}
`,
  };
}

function cFunctionReturnVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int double_value(int value) {
    return value * 2;
}

int main(void) {
    int result = double_value(6);
    printf("%d\\n", result);
    return 0;
}
`,
    implement: `#include <stdio.h>

int double_value(int value) {
    /* TODO: return value multiplied by 2. */
    return value;
}

int main(void) {
    printf("%d\\n", double_value(6));
    return 0;
}
`,
  };
}

function javaFunctionReturnVariant(): CodeVariant {
  return {
    learn: `public class Main {
    static int doubleValue(int value) {
        return value * 2;
    }

    public static void main(String[] args) {
        int result = doubleValue(6);
        System.out.println(result);
    }
}
`,
    implement: `public class Main {
    static int doubleValue(int value) {
        // TODO: return value multiplied by 2.
        return value;
    }

    public static void main(String[] args) {
        System.out.println(doubleValue(6));
    }
}
`,
  };
}

function javaLambdaFunctionsVariant(): CodeVariant {
  return {
    learn: `import java.util.*;
import java.util.function.IntUnaryOperator;

public class Main {
    public static void main(String[] args) {
        IntUnaryOperator doubleValue = value -> value * 2;
        int[] numbers = {1, 2, 3};
        List<Integer> result = new ArrayList<>();
        for (int number : numbers) {
            result.add(doubleValue.applyAsInt(number));
        }
        System.out.println(result);
    }
}
`,
    implement: `import java.util.function.IntUnaryOperator;

public class Main {
    static int applyTwice(int value) {
        IntUnaryOperator doubleValue = x -> x * 2;
        // TODO: use the lambda to transform value.
        return value;
    }

    public static void main(String[] args) {
        System.out.println(applyTwice(3));
    }
}
`,
  };
}

function cInputParsingVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>
#include <stdlib.h>

int main(void) {
    const char *text = "42";
    int value = atoi(text);
    printf("%d\\n", value + 8);
    return 0;
}
`,
    implement: `#include <stdio.h>
#include <stdlib.h>

int parse_and_add(const char *text, int delta) {
    /* TODO: convert text to int and add delta. */
    return 0;
}

int main(void) {
    printf("%d\\n", parse_and_add("42", 8));
    return 0;
}
`,
  };
}

function javaInputParsingVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        String text = "42";
        int value = Integer.parseInt(text);
        System.out.println(value + 8);
    }
}
`,
    implement: `public class Main {
    static int parseAndAdd(String text, int delta) {
        // TODO: convert text to int and add delta.
        return 0;
    }

    public static void main(String[] args) {
        System.out.println(parseAndAdd("42", 8));
    }
}
`,
  };
}

function cArrayCellsVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int items[5] = {10, 20, 30, 40, 0};
    int first = items[0];
    items[2] = first + 5;
    items[4] = 50;
    for (int i = 0; i < 5; i++) {
        printf("%d ", items[i]);
    }
    printf("\\n");
    return 0;
}
`,
    implement: `#include <stdio.h>

void swap_edges(int items[], int n) {
    /* TODO: swap the first and last values. */
}

int main(void) {
    int items[] = {1, 2, 3, 4};
    swap_edges(items, 4);
    for (int i = 0; i < 4; i++) {
        printf("%d ", items[i]);
    }
    printf("\\n");
    return 0;
}
`,
  };
}

function javaArrayCellsVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        int[] items = {10, 20, 30, 40, 0};
        int first = items[0];
        items[2] = first + 5;
        items[4] = 50;
        System.out.println(Arrays.toString(items));
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static int[] swapEdges(int[] items) {
        int[] result = Arrays.copyOf(items, items.length);
        // TODO: swap the first and last values.
        return result;
    }

    public static void main(String[] args) {
        int[] items = {1, 2, 3, 4};
        System.out.println(Arrays.toString(swapEdges(items)));
    }
}
`,
  };
}

function cLinearSearchVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int numbers[] = {4, 2, 7, 1};
    int target = 7;
    int found_index = -1;
    for (int i = 0; i < 4; i++) {
        if (numbers[i] == target) {
            found_index = i;
            break;
        }
    }
    printf("%d\\n", found_index);
    return 0;
}
`,
    implement: `#include <stdio.h>

int linear_search(int numbers[], int n, int target) {
    /* TODO: scan from left to right and return the index. */
    return -1;
}

int main(void) {
    int numbers[] = {4, 2, 7, 1};
    printf("%d\\n", linear_search(numbers, 4, 7));
    return 0;
}
`,
  };
}

function javaLinearSearchVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        int[] numbers = {4, 2, 7, 1};
        int target = 7;
        int foundIndex = -1;
        for (int i = 0; i < numbers.length; i++) {
            if (numbers[i] == target) {
                foundIndex = i;
                break;
            }
        }
        System.out.println(foundIndex);
    }
}
`,
    implement: `public class Main {
    static int linearSearch(int[] numbers, int target) {
        // TODO: scan from left to right and return the index.
        return -1;
    }

    public static void main(String[] args) {
        int[] numbers = {4, 2, 7, 1};
        System.out.println(linearSearch(numbers, 7));
    }
}
`,
  };
}

function cHashMapCountingVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>
#include <string.h>

int main(void) {
    const char *words[] = {"red", "blue", "red", "green", "blue", "red"};
    const char *keys[] = {"red", "blue", "green"};
    int counts[3] = {0};
    for (int i = 0; i < 6; i++) {
        for (int k = 0; k < 3; k++) {
            if (strcmp(words[i], keys[k]) == 0) {
                counts[k]++;
            }
        }
    }
    for (int k = 0; k < 3; k++) {
        printf("%s:%d ", keys[k], counts[k]);
    }
    printf("\\n");
    return 0;
}
`,
    implement: `#include <stdio.h>
#include <string.h>

void count_words(const char *words[], int n, const char *keys[], int counts[], int key_count) {
    /* TODO: count each key in words. */
}

int main(void) {
    const char *words[] = {"red", "blue", "red"};
    const char *keys[] = {"red", "blue"};
    int counts[2] = {0};
    count_words(words, 3, keys, counts, 2);
    printf("red:%d blue:%d\\n", counts[0], counts[1]);
    return 0;
}
`,
  };
}

function javaHashMapCountingVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        String[] words = {"red", "blue", "red", "green", "blue", "red"};
        Map<String, Integer> counts = new LinkedHashMap<>();
        for (String word : words) {
            counts.put(word, counts.getOrDefault(word, 0) + 1);
        }
        System.out.println(counts);
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static Map<String, Integer> countWords(String[] words) {
        Map<String, Integer> counts = new LinkedHashMap<>();
        // TODO: count each word.
        return counts;
    }

    public static void main(String[] args) {
        String[] words = {"red", "blue", "red"};
        System.out.println(countWords(words));
    }
}
`,
  };
}

function cDequeVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int deque[8] = {0};
    int front = 3;
    int rear = 3;
    deque[rear++] = 2;
    deque[rear++] = 3;
    deque[--front] = 1;
    deque[rear++] = 4;
    front++;
    rear--;
    for (int i = front; i < rear; i++) {
        printf("%d ", deque[i]);
    }
    printf("\\n");
    return 0;
}
`,
    implement: `#include <stdio.h>

void trim_deque(int result[], int *n) {
    /* TODO: model both-end insertions and removals. */
    *n = 0;
}

int main(void) {
    int result[4];
    int n;
    trim_deque(result, &n);
    for (int i = 0; i < n; i++) {
        printf("%d ", result[i]);
    }
    printf("\\n");
    return 0;
}
`,
  };
}

function javaDequeVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        Deque<Integer> items = new ArrayDeque<>();
        items.addLast(2);
        items.addLast(3);
        items.addFirst(1);
        items.addLast(4);
        int left = items.removeFirst();
        int right = items.removeLast();
        System.out.println(items + " " + left + " " + right);
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static Deque<Integer> trimDeque() {
        Deque<Integer> items = new ArrayDeque<>();
        items.addLast(2);
        items.addLast(3);
        // TODO: add both ends, then remove both ends.
        return items;
    }

    public static void main(String[] args) {
        System.out.println(trimDeque());
    }
}
`,
  };
}

function cArraySortVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int numbers[] = {5, 2, 4, 6, 1, 3};
    int n = 6;

    for (int i = 1; i < n; i++) {
        int key = numbers[i];
        int j = i - 1;
        while (j >= 0 && numbers[j] > key) {
            numbers[j + 1] = numbers[j];
            j--;
        }
        numbers[j + 1] = key;
    }

    for (int i = 0; i < n; i++) {
        printf("%d ", numbers[i]);
    }
    printf("\\n");
    return 0;
}
`,
    implement: `#include <stdio.h>

void insertion_sort(int numbers[], int n) {
    /* TODO: sort numbers in ascending order. */
}

int main(void) {
    int numbers[] = {5, 2, 4, 6, 1, 3};
    int n = 6;
    insertion_sort(numbers, n);
    for (int i = 0; i < n; i++) {
        printf("%d ", numbers[i]);
    }
    printf("\\n");
    return 0;
}
`,
  };
}

function javaArraySortVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        int[] numbers = {5, 2, 4, 6, 1, 3};

        for (int i = 1; i < numbers.length; i++) {
            int key = numbers[i];
            int j = i - 1;
            while (j >= 0 && numbers[j] > key) {
                numbers[j + 1] = numbers[j];
                j--;
            }
            numbers[j + 1] = key;
        }

        System.out.println(Arrays.toString(numbers));
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static int[] insertionSort(int[] numbers) {
        int[] items = Arrays.copyOf(numbers, numbers.length);
        // TODO: sort items in ascending order.
        return items;
    }

    public static void main(String[] args) {
        int[] numbers = {5, 2, 4, 6, 1, 3};
        System.out.println(Arrays.toString(insertionSort(numbers)));
    }
}
`,
  };
}

function javaMergeSortShowcaseVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    static void mergeSort(int[] numbers, int start, int end) {
        if (end - start <= 1) {
            return;
        }

        int mid = (start + end) / 2;
        mergeSort(numbers, start, mid);
        mergeSort(numbers, mid, end);

        int[] temp = new int[end - start];
        int left = start;
        int right = mid;
        int index = 0;

        while (left < mid && right < end) {
            if (numbers[left] <= numbers[right]) {
                temp[index++] = numbers[left++];
            } else {
                temp[index++] = numbers[right++];
            }
        }

        while (left < mid) {
            temp[index++] = numbers[left++];
        }

        while (right < end) {
            temp[index++] = numbers[right++];
        }

        for (int i = 0; i < temp.length; i++) {
            numbers[start + i] = temp[i];
        }
    }

    public static void main(String[] args) {
        int[] numbers = {27, 10, 12, 20, 25, 13, 15, 22};
        mergeSort(numbers, 0, numbers.length);
        System.out.println(Arrays.toString(numbers));
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static void mergeSort(int[] numbers, int start, int end) {
        // TODO: 배열을 나누고, 양쪽을 정렬한 뒤 병합하세요.
    }

    public static void main(String[] args) {
        int[] numbers = {27, 10, 12, 20, 25, 13, 15, 22};
        mergeSort(numbers, 0, numbers.length);
        System.out.println(Arrays.toString(numbers));
    }
}
`,
  };
}

function cRadixSortShowcaseVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int numbers[] = {8, 2, 7, 3, 5};
    int output[5] = {0};
    int buckets[10][5] = {0};
    int counts[10] = {0};
    int n = 5;

    for (int i = 0; i < n; i++) {
        int digit = numbers[i] % 10;
        buckets[digit][counts[digit]] = numbers[i];
        counts[digit]++;
    }

    int index = 0;
    for (int digit = 0; digit < 10; digit++) {
        for (int j = 0; j < counts[digit]; j++) {
            output[index++] = buckets[digit][j];
        }
    }

    for (int i = 0; i < n; i++) {
        printf("%d ", output[i]);
    }
    printf("\\n");
    return 0;
}
`,
    implement: `#include <stdio.h>

void radix_sort_one_digit(int numbers[], int output[], int n) {
    /* TODO: 각 값을 자릿수 버킷에 넣고, 버킷을 순서대로 병합하세요. */
}

int main(void) {
    int numbers[] = {8, 2, 7, 3, 5};
    int output[5] = {0};
    radix_sort_one_digit(numbers, output, 5);
    for (int i = 0; i < 5; i++) {
        printf("%d ", output[i]);
    }
    printf("\\n");
    return 0;
}
`,
  };
}

function cBinarySearchVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int numbers[] = {1, 3, 5, 7, 9, 11};
    int target = 7;
    int low = 0;
    int high = 5;

    while (low <= high) {
        int mid = (low + high) / 2;
        if (numbers[mid] == target) {
            printf("%d\\n", mid);
            break;
        }
        if (numbers[mid] < target) {
            low = mid + 1;
        } else {
            high = mid - 1;
        }
    }
    return 0;
}
`,
    implement: `#include <stdio.h>

int binary_search(int numbers[], int n, int target) {
    int low = 0;
    int high = n - 1;
    /* TODO: return the target index, or -1. */
    return -1;
}

int main(void) {
    int numbers[] = {1, 3, 5, 7, 9};
    printf("%d\\n", binary_search(numbers, 5, 7));
    return 0;
}
`,
  };
}

function javaBinarySearchVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        int[] numbers = {1, 3, 5, 7, 9, 11};
        int target = 7;
        int low = 0;
        int high = numbers.length - 1;

        while (low <= high) {
            int mid = (low + high) / 2;
            if (numbers[mid] == target) {
                System.out.println(mid);
                break;
            }
            if (numbers[mid] < target) {
                low = mid + 1;
            } else {
                high = mid - 1;
            }
        }
    }
}
`,
    implement: `public class Main {
    static int binarySearch(int[] numbers, int target) {
        int low = 0;
        int high = numbers.length - 1;
        // TODO: return the target index, or -1.
        return -1;
    }

    public static void main(String[] args) {
        int[] numbers = {1, 3, 5, 7, 9};
        System.out.println(binarySearch(numbers, 7));
    }
}
`,
  };
}

function cTwoPointersVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int numbers[] = {1, 2, 4, 7, 11, 15};
    int target = 15;
    int left = 0;
    int right = 5;

    while (left < right) {
        int current = numbers[left] + numbers[right];
        if (current == target) {
            printf("%d %d\\n", left, right);
            break;
        }
        if (current < target) {
            left++;
        } else {
            right--;
        }
    }
    return 0;
}
`,
    implement: `#include <stdio.h>

void two_sum_sorted(int numbers[], int n, int target, int result[]) {
    int left = 0;
    int right = n - 1;
    result[0] = -1;
    result[1] = -1;
    /* TODO: move two pointers until the target sum is found. */
}

int main(void) {
    int numbers[] = {1, 2, 4, 7, 11, 15};
    int result[2];
    two_sum_sorted(numbers, 6, 15, result);
    printf("%d %d\\n", result[0], result[1]);
    return 0;
}
`,
  };
}

function javaTwoPointersVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        int[] numbers = {1, 2, 4, 7, 11, 15};
        int target = 15;
        int left = 0;
        int right = numbers.length - 1;

        while (left < right) {
            int current = numbers[left] + numbers[right];
            if (current == target) {
                System.out.println(left + " " + right);
                break;
            }
            if (current < target) {
                left++;
            } else {
                right--;
            }
        }
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static int[] twoSumSorted(int[] numbers, int target) {
        int left = 0;
        int right = numbers.length - 1;
        // TODO: move two pointers until the target sum is found.
        return new int[] {-1, -1};
    }

    public static void main(String[] args) {
        int[] numbers = {1, 2, 4, 7, 11, 15};
        System.out.println(Arrays.toString(twoSumSorted(numbers, 15)));
    }
}
`,
  };
}

function cSlidingWindowVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int numbers[] = {2, 1, 5, 1, 3, 2};
    int k = 3;
    int window_sum = 0;
    for (int i = 0; i < k; i++) {
        window_sum += numbers[i];
    }
    int best = window_sum;
    for (int right = k; right < 6; right++) {
        window_sum += numbers[right] - numbers[right - k];
        if (window_sum > best) {
            best = window_sum;
        }
    }
    printf("%d\\n", best);
    return 0;
}
`,
    implement: `#include <stdio.h>

int max_window_sum(int numbers[], int n, int k) {
    int best = 0;
    /* TODO: compute the best fixed-size window sum. */
    return best;
}

int main(void) {
    int numbers[] = {2, 1, 5, 1, 3, 2};
    printf("%d\\n", max_window_sum(numbers, 6, 3));
    return 0;
}
`,
  };
}

function javaSlidingWindowVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        int[] numbers = {2, 1, 5, 1, 3, 2};
        int k = 3;
        int windowSum = 0;
        for (int i = 0; i < k; i++) {
            windowSum += numbers[i];
        }
        int best = windowSum;
        for (int right = k; right < numbers.length; right++) {
            windowSum += numbers[right] - numbers[right - k];
            best = Math.max(best, windowSum);
        }
        System.out.println(best);
    }
}
`,
    implement: `public class Main {
    static int maxWindowSum(int[] numbers, int k) {
        int best = 0;
        // TODO: compute the best fixed-size window sum.
        return best;
    }

    public static void main(String[] args) {
        int[] numbers = {2, 1, 5, 1, 3, 2};
        System.out.println(maxWindowSum(numbers, 3));
    }
}
`,
  };
}

function cPrefixSumVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int numbers[] = {3, 1, 4, 1};
    int prefix[4];
    int running = 0;
    for (int i = 0; i < 4; i++) {
        running += numbers[i];
        prefix[i] = running;
    }
    for (int i = 0; i < 4; i++) {
        printf("%d ", prefix[i]);
    }
    printf("\\n");
    return 0;
}
`,
    implement: `#include <stdio.h>

void build_prefix_sum(int numbers[], int n, int prefix[]) {
    int running = 0;
    /* TODO: fill prefix with running sums. */
}

int main(void) {
    int numbers[] = {3, 1, 4, 1};
    int prefix[4] = {0};
    build_prefix_sum(numbers, 4, prefix);
    for (int i = 0; i < 4; i++) {
        printf("%d ", prefix[i]);
    }
    printf("\\n");
    return 0;
}
`,
  };
}

function javaPrefixSumVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        int[] numbers = {3, 1, 4, 1};
        int[] prefix = new int[numbers.length];
        int running = 0;
        for (int i = 0; i < numbers.length; i++) {
            running += numbers[i];
            prefix[i] = running;
        }
        System.out.println(Arrays.toString(prefix));
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static int[] buildPrefixSum(int[] numbers) {
        int[] prefix = new int[numbers.length];
        int running = 0;
        // TODO: fill prefix with running sums.
        return prefix;
    }

    public static void main(String[] args) {
        int[] numbers = {3, 1, 4, 1};
        System.out.println(Arrays.toString(buildPrefixSum(numbers)));
    }
}
`,
  };
}

function cPalindromeVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>
#include <string.h>
#include <stdbool.h>

int main(void) {
    char text[] = "level";
    int left = 0;
    int right = (int)strlen(text) - 1;
    bool is_palindrome = true;
    while (left < right) {
        if (text[left] != text[right]) {
            is_palindrome = false;
            break;
        }
        left++;
        right--;
    }
    printf("%s\\n", is_palindrome ? "true" : "false");
    return 0;
}
`,
    implement: `#include <stdio.h>
#include <string.h>
#include <stdbool.h>

bool is_palindrome(char text[]) {
    int left = 0;
    int right = (int)strlen(text) - 1;
    /* TODO: compare both ends. */
    return true;
}

int main(void) {
    char text[] = "level";
    printf("%s\\n", is_palindrome(text) ? "true" : "false");
    return 0;
}
`,
  };
}

function javaPalindromeVariant(): CodeVariant {
  return {
    learn: `public class Main {
    public static void main(String[] args) {
        String text = "level";
        int left = 0;
        int right = text.length() - 1;
        boolean isPalindrome = true;
        while (left < right) {
            if (text.charAt(left) != text.charAt(right)) {
                isPalindrome = false;
                break;
            }
            left++;
            right--;
        }
        System.out.println(isPalindrome);
    }
}
`,
    implement: `public class Main {
    static boolean isPalindrome(String text) {
        int left = 0;
        int right = text.length() - 1;
        // TODO: compare both ends.
        return true;
    }

    public static void main(String[] args) {
        System.out.println(isPalindrome("level"));
    }
}
`,
  };
}

function cStackVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int stack[8];
    int top = 0;
    stack[top++] = 1;
    stack[top++] = 2;
    stack[top++] = 3;
    top--;
    for (int i = 0; i < top; i++) {
        printf("%d ", stack[i]);
    }
    printf("\\n");
    return 0;
}
`,
    implement: `#include <stdio.h>

int build_stack(int stack[]) {
    int top = 0;
    /* TODO: push 1, 2, 3, then pop once. */
    return top;
}

int main(void) {
    int stack[8];
    int top = build_stack(stack);
    for (int i = 0; i < top; i++) {
        printf("%d ", stack[i]);
    }
    printf("\\n");
    return 0;
}
`,
  };
}

function javaStackVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(1);
        stack.push(2);
        stack.push(3);
        stack.pop();
        System.out.println(stack);
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static Deque<Integer> buildStack() {
        Deque<Integer> stack = new ArrayDeque<>();
        // TODO: push 1, 2, 3, then pop once.
        return stack;
    }

    public static void main(String[] args) {
        System.out.println(buildStack());
    }
}
`,
  };
}

function cQueueVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int queue[8] = {1};
    int front = 0;
    int rear = 1;
    queue[rear++] = 2;
    queue[rear++] = 3;
    front++;
    for (int i = front; i < rear; i++) {
        printf("%d ", queue[i]);
    }
    printf("\\n");
    return 0;
}
`,
    implement: `#include <stdio.h>

void build_queue(int queue[], int *front, int *rear) {
    *front = 0;
    *rear = 0;
    /* TODO: enqueue 1, 2, 3, then dequeue once. */
}

int main(void) {
    int queue[8];
    int front;
    int rear;
    build_queue(queue, &front, &rear);
    for (int i = front; i < rear; i++) {
        printf("%d ", queue[i]);
    }
    printf("\\n");
    return 0;
}
`,
  };
}

function javaQueueVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        Queue<Integer> queue = new LinkedList<>();
        queue.offer(1);
        queue.offer(2);
        queue.offer(3);
        queue.poll();
        System.out.println(queue);
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static Queue<Integer> buildQueue() {
        Queue<Integer> queue = new LinkedList<>();
        // TODO: enqueue 1, 2, 3, then dequeue once.
        return queue;
    }

    public static void main(String[] args) {
        System.out.println(buildQueue());
    }
}
`,
  };
}

function cRecursionVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

int main(void) {
    printf("%d\\n", factorial(4));
    return 0;
}
`,
    implement: `#include <stdio.h>

int factorial(int n) {
    /* TODO: implement the recursive factorial. */
    return 1;
}

int main(void) {
    printf("%d\\n", factorial(4));
    return 0;
}
`,
  };
}

function javaRecursionVariant(): CodeVariant {
  return {
    learn: `public class Main {
    static int factorial(int n) {
        if (n <= 1) {
            return 1;
        }
        return n * factorial(n - 1);
    }

    public static void main(String[] args) {
        System.out.println(factorial(4));
    }
}
`,
    implement: `public class Main {
    static int factorial(int n) {
        // TODO: implement the recursive factorial.
        return 1;
    }

    public static void main(String[] args) {
        System.out.println(factorial(4));
    }
}
`,
  };
}

function cDpVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

int main(void) {
    int dp[3][3] = {0};
    dp[0][0] = 1;
    dp[0][1] = 1;
    dp[1][1] = dp[0][1] + 1;
    dp[1][2] = dp[1][1] + 1;
    dp[2][2] = dp[1][2] + 1;

    for (int r = 0; r < 3; r++) {
        for (int c = 0; c < 3; c++) {
            printf("%d ", dp[r][c]);
        }
        printf("\\n");
    }
    return 0;
}
`,
    implement: `#include <stdio.h>

void build_dp_table(int dp[3][3]) {
    /* TODO: fill the DP table. */
}

int main(void) {
    int dp[3][3] = {0};
    build_dp_table(dp);
    for (int r = 0; r < 3; r++) {
        for (int c = 0; c < 3; c++) {
            printf("%d ", dp[r][c]);
        }
        printf("\\n");
    }
    return 0;
}
`,
  };
}

function javaDpVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        int[][] dp = new int[3][3];
        dp[0][0] = 1;
        dp[0][1] = 1;
        dp[1][1] = dp[0][1] + 1;
        dp[1][2] = dp[1][1] + 1;
        dp[2][2] = dp[1][2] + 1;
        System.out.println(Arrays.deepToString(dp));
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static int[][] buildDpTable() {
        int[][] dp = new int[3][3];
        // TODO: fill the DP table.
        return dp;
    }

    public static void main(String[] args) {
        System.out.println(Arrays.deepToString(buildDpTable()));
    }
}
`,
  };
}

function cTreeVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>

typedef struct Node {
    int value;
    struct Node *left;
    struct Node *right;
} Node;

int main(void) {
    Node left = {5, NULL, NULL};
    Node right = {15, NULL, NULL};
    Node root = {10, &left, &right};
    printf("%d\\n", root.value);
    return 0;
}
`,
    implement: `#include <stdio.h>

typedef struct Node {
    int value;
    struct Node *left;
    struct Node *right;
} Node;

int main(void) {
    Node root = {10, NULL, NULL};
    /* TODO: connect left child 5 and right child 15. */
    printf("%d\\n", root.value);
    return 0;
}
`,
  };
}

function javaTreeVariant(): CodeVariant {
  return {
    learn: `public class Main {
    static class Node {
        int value;
        Node left;
        Node right;
        Node(int value) {
            this.value = value;
        }
    }

    public static void main(String[] args) {
        Node root = new Node(10);
        root.left = new Node(5);
        root.right = new Node(15);
        System.out.println(root.value);
    }
}
`,
    implement: `public class Main {
    static class Node {
        int value;
        Node left;
        Node right;
        Node(int value) {
            this.value = value;
        }
    }

    static Node buildTree() {
        Node root = new Node(10);
        // TODO: connect left child 5 and right child 15.
        return root;
    }

    public static void main(String[] args) {
        System.out.println(buildTree().value);
    }
}
`,
  };
}

function cGraphVariant(): CodeVariant {
  return {
    learn: `#include <stdio.h>
#include <stdbool.h>

int main(void) {
    int graph[5][5] = {0};
    graph[0][1] = 1;
    graph[0][2] = 1;
    graph[1][3] = 1;
    graph[2][4] = 1;

    int queue[8] = {0};
    int front = 0;
    int rear = 1;
    bool visited[5] = {false};

    while (front < rear) {
        int node = queue[front++];
        if (visited[node]) {
            continue;
        }
        visited[node] = true;
        printf("%d ", node);
        for (int next = 0; next < 5; next++) {
            if (graph[node][next] && !visited[next]) {
                queue[rear++] = next;
            }
        }
    }
    printf("\\n");
    return 0;
}
`,
    implement: `#include <stdio.h>
#include <stdbool.h>

void bfs(int graph[5][5], int start) {
    int queue[8] = {start};
    int front = 0;
    int rear = 1;
    bool visited[5] = {false};
    /* TODO: print BFS order. */
}

int main(void) {
    int graph[5][5] = {0};
    graph[0][1] = 1;
    graph[0][2] = 1;
    graph[1][3] = 1;
    graph[2][4] = 1;
    bfs(graph, 0);
    return 0;
}
`,
  };
}

function javaGraphVariant(): CodeVariant {
  return {
    learn: `import java.util.*;

public class Main {
    public static void main(String[] args) {
        int[][] edges = {
            {1, 2},
            {1, 3},
            {2, 4},
            {3, 5}
        };

        Queue<Integer> queue = new LinkedList<>();
        List<Integer> visited = new ArrayList<>();
        queue.offer(1);

        while (!queue.isEmpty()) {
            int node = queue.poll();
            if (visited.contains(node)) {
                continue;
            }
            visited.add(node);
            for (int i = 0; i < edges.length; i++) {
                if (edges[i][0] == node) {
                    queue.offer(edges[i][1]);
                }
            }
        }
        System.out.println(visited);
    }
}
`,
    implement: `import java.util.*;

public class Main {
    static List<Integer> bfsOrder(int[][] edges, int start) {
        Queue<Integer> queue = new LinkedList<>();
        List<Integer> visited = new ArrayList<>();
        queue.offer(start);
        // TODO: implement BFS order.
        return visited;
    }

    public static void main(String[] args) {
        int[][] edges = {
            {1, 2},
            {1, 3},
            {2, 4},
            {3, 5}
        };
        System.out.println(bfsOrder(edges, 1));
    }
}
`,
  };
}
