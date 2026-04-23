fn is_even(n:i32) -> bool {
  if (n == 0) {
    return true;
  }
  if (n == 1) {
    return false;
  }
  return is_even(n - 2);
}

fn sum_to(n:i32) -> i32 {
  let mut total:i32;
  let mut i:i32;
  total = 0;
  i = 1;
  while (i < n + 1) {
    total = total + i;
    i = i + 1;
  }
  return total;
}

fn power(base:i32, exp:i32) -> i32 {
  if (exp == 0) {
    return 1;
  }
  return base * power(base, exp - 1);
}

fn main() -> () {
  println!(is_even(10));
  println!(is_even(7));
  println!(sum_to(10));
  println!(sum_to(100));
  println!(power(2, 10));
  println!(power(3, 4));
}
